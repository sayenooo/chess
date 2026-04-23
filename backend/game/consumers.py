import logging
import time
from typing import ClassVar
from urllib.parse import parse_qs
from .bot import ChessBot
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from game.engine.board import Board, parse_square, format_square
from game.models import Game, Move
from game.serializers import MoveInputSerializer

logger = logging.getLogger(__name__)


class ChessConsumer(AsyncJsonWebsocketConsumer):
    """
    Три режима:
    - SOLO   — один игрок ходит за обе стороны (без group layer)
    - ONLINE — два игрока в одной комнате
    - BOT    — игрок vs бот

    Подключение:
        ws://host/ws/game/<room_name>/?type=solo
        ws://host/ws/game/<room_name>/?type=online  (по умолчанию)

    Life cycle:
    ---
    1. connect()    — клиент подключается, получает начальное состояние
    2. receive_json — клиент отправляет action ('move' / 'resign' / 'get_state')
    3. disconnect() — клиент отключается
    """

    active_boards: ClassVar[dict[str, Board]] = {}
    _draw_offered_by: ClassVar[dict[str, str]] = {}  # room_name -> color that offered
    _last_move_ts: ClassVar[dict[str, float]] = {}    # room_name -> timestamp of last move

    async def connect(self):
        self.user = self.scope['user']
        
        if self.user.is_anonymous:
            await self.close()
            return

        self.room_name: str = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'

        game = await self.get_game()
        if not game:
            await self.close()
            return

        self.game_type = game.game_type

        if self.game_type == 'ONLINE':
            if game.player_white and game.player_white.user == self.user:
                self.user_color = 'white'
            elif game.player_black and game.player_black.user == self.user:
                self.user_color = 'black'
            else:
                await self.close()
                return
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        elif self.game_type == 'SOLO':
            if game.player_white and game.player_white.user == self.user:
                self.user_color = 'both'
            else:
                await self.close()
                return
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        elif self.game_type == 'BOT':
            if game.player_white and game.player_white.user == self.user:
                self.user_color = 'white'
            elif game.player_black and game.player_black.user == self.user:
                self.user_color = 'black'
            else:
                await self.close()
                return
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        if self.room_name not in self.active_boards:
            # Rebuild board from saved moves (for rejoin after server restart)
            board = Board()
            moves = await self._get_saved_moves()
            for m in moves:
                try:
                    fr, fc = parse_square(m['from_square'])
                    tr, tc = parse_square(m['to_square'])
                    board.move_piece((fr, fc), (tr, tc), m.get('promotion', 'Queen'))
                except Exception:
                    pass
            self.active_boards[self.room_name] = board
        self.board = self.active_boards[self.room_name]

        # Init move timestamp for timer if not set
        if self.room_name not in self._last_move_ts:
            self._last_move_ts[self.room_name] = time.time()

        await self.accept()
        
        await self.send_json({
            'type': 'connection_established',
            'color': self.user_color,
            'game_type': self.game_type,
            'white_time': game.white_time_remaining,
            'black_time': game.black_time_remaining,
            'current_turn': self.board.current_turn,
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )
            logger.info('Player disconnected from room %s', self.room_group_name)

        # Clean up board when everyone disconnects (solo always cleans up)
        if getattr(self, 'game_type', None) == 'SOLO' and hasattr(self, 'room_name'):
            self.active_boards.pop(self.room_name, None)

    async def receive_json(self, content: dict):
        """
        JSON from frontend.

        Message format:
        {
            "action": "move" | "resign" | "get_state" | "new_game",
            "from_square": "e2",     // only for move
            "to_square": "e4",       // only for move
            "promotion": "Queen"     // optional, only for move
        }
        """
        action = content.get('action')

        match action:
            case 'move':
                await self._handle_move(content)
            case 'resign':
                await self._handle_resign()
            case 'new_game':
                await self._handle_new_game()
            case 'offer_draw':
                await self._handle_offer_draw()
            case 'respond_draw':
                await self._handle_respond_draw(content.get('accepted', False))
            case 'get_state':
                game = await self.get_game()
                if not game:
                    return
                await self.send_json({
                    'type': 'game_state',
                    'game_type': getattr(self, 'game_type', 'UNKNOWN'),
                    'payload': {
                        'fen': game.current_fen,
                        'current_turn': self.board.current_turn,
                        'status': game.status,
                        'white_time': game.white_time_remaining,
                        'black_time': game.black_time_remaining,
                    },
                })
            case _:
                await self.send_json({
                    'type': 'error',
                    'payload': {
                        'message': f'Unknown action: {action}',
                        'valid_actions': ['move', 'resign', 'get_state', 'new_game', 'offer_draw', 'respond_draw'],
                    },
                })
    
    @database_sync_to_async
    def get_game(self):
        if not hasattr(self, 'room_name'):
            return None
        try:
            # Looking for the game by ID and get users
            return Game.objects.select_related(
                'player_white__user',
                'player_black__user'
            ).get(id=self.room_name)
        except (Game.DoesNotExist, ValueError):
            return None

    @database_sync_to_async
    def _get_saved_moves(self):
        """Get saved moves from DB to rebuild board state."""
        try:
            return list(
                Move.objects.filter(game_id=self.room_name)
                .order_by('move_number', 'id')
                .values('from_square', 'to_square', 'promotion')
            )
        except Exception:
            return []

    @database_sync_to_async
    def _update_ratings(self, game, winner_color=None, is_draw=False):
        """Update player ratings and stats after an ONLINE game ends."""
        if game.game_type != 'ONLINE':
            return
        
        white = game.player_white
        black = game.player_black
        if not white or not black:
            return

        RATING_DELTA = 15

        if is_draw:
            white.draws += 1
            black.draws += 1
            white.save()
            black.save()
        elif winner_color == 'white':
            white.rating += RATING_DELTA
            white.wins += 1
            black.rating = max(0, black.rating - RATING_DELTA)
            black.losses += 1
            white.save()
            black.save()
        elif winner_color == 'black':
            black.rating += RATING_DELTA
            black.wins += 1
            white.rating = max(0, white.rating - RATING_DELTA)
            white.losses += 1
            white.save()
            black.save()

    def _compute_notation(self, piece, from_row, from_col, to_row, to_col, captured_piece, promotion, is_check, is_checkmate):
        """Compute standard algebraic notation for a move."""
        piece_name = piece.__class__.__name__

        # Castling
        if piece_name == 'King' and abs(from_col - to_col) == 2:
            notation = 'O-O' if to_col == 6 else 'O-O-O'
            if is_checkmate:
                notation += '#'
            elif is_check:
                notation += '+'
            return notation

        parts = []

        # Piece letter (no letter for pawn)
        piece_letters = {'King': 'K', 'Queen': 'Q', 'Rook': 'R', 'Bishop': 'B', 'Knight': 'N'}
        if piece_name in piece_letters:
            parts.append(piece_letters[piece_name])

            # Disambiguation: check if another piece of same type+color can reach the same square
            for r in range(8):
                for c in range(8):
                    if (r, c) == (from_row, from_col):
                        continue
                    other = self.board.get_piece_at(r, c)
                    if other and other.__class__.__name__ == piece_name and other.color == piece.color:
                        other_moves = other.get_legal_moves(self.board)
                        if (to_row, to_col) in other_moves:
                            if from_col != c:
                                parts.append(format_square(from_row, from_col)[0])  # file
                            elif from_row != r:
                                parts.append(format_square(from_row, from_col)[1])  # rank
                            else:
                                parts.append(format_square(from_row, from_col))
                            break

        # Pawn captures need the file
        if piece_name == 'Pawn' and captured_piece:
            parts.append(format_square(from_row, from_col)[0])

        # Capture
        if captured_piece:
            parts.append('x')

        # Destination square
        parts.append(format_square(to_row, to_col))

        # Promotion
        if piece_name == 'Pawn' and (to_row == 7 or to_row == 0):
            promo_letters = {'Queen': 'Q', 'Rook': 'R', 'Bishop': 'B', 'Knight': 'N'}
            parts.append('=' + promo_letters.get(promotion, 'Q'))

        # Check / Checkmate
        if is_checkmate:
            parts.append('#')
        elif is_check:
            parts.append('+')

        return ''.join(parts)

    async def _handle_move(self, content: dict, is_bot=False):
        # Game status check
        game = await self.get_game()
        if not game:
            return
            
        if game.status in [Game.Status.CHECKMATE, Game.Status.STALEMATE, Game.Status.DRAW, Game.Status.RESIGNED]:
            if not is_bot:
                await self.send_json({
                    'type': 'error',
                    'payload': {'message': 'The game is already over, you can\'t make any moves!'}
                })
            return

        current_turn = self.board.current_turn
        
        if not is_bot and self.user_color != 'both' and self.user_color != current_turn:
            await self.send_json({
                'type': 'error',
                'payload': {
                    'message': f'It\'s not your turn right now! You\'re playing for {self.user_color}, but now it is {current_turn}\'s turn.'
                }
            })
            return

        serializer = MoveInputSerializer(data=content)
        if not serializer.is_valid():
            await self.send_json({
                'type': 'error',
                'payload': {
                    'message': 'Incorrect move format',
                    'details': serializer.errors,
                },
            })
            return

        from_sq = serializer.validated_data['from_square']
        to_sq = serializer.validated_data['to_square']
        promotion = serializer.validated_data.get('promotion', 'Queen')

        try:
            from_row, from_col = parse_square(from_sq)
            to_row, to_col = parse_square(to_sq)

            piece = self.board.get_piece_at(from_row, from_col)
            if not piece:
                await self.send_json({
                    'type': 'error', 
                    'payload': {
                        'message': 'No piece at from_square'
                        },
                })
                return

            legal_moves = piece.get_legal_moves(self.board)
            if (to_row, to_col) not in legal_moves:
                await self.send_json({
                    'type': 'error', 
                    'payload': {
                        'message': 'Illegal move'
                        }
                })
                return

            piece_name = piece.__class__.__name__
            captured_piece = self.board.move_piece((from_row, from_col), (to_row, to_col), promotion)
            captured_name = captured_piece.__class__.__name__ if captured_piece else ''
            new_fen = self.board.get_fen()
            is_check = self.board.is_in_check(self.board.current_turn)
            is_checkmate = self.board.is_checkmate(self.board.current_turn)
            is_stalemate = self.board.is_stalemate(self.board.current_turn)

            # Compute algebraic notation
            notation = self._compute_notation(
                piece, from_row, from_col, to_row, to_col,
                captured_piece, promotion, is_check, is_checkmate
            )

            # Clear any pending draw offer on a new move
            self._draw_offered_by.pop(self.room_name, None)

            # Timer deduction
            now = time.time()
            elapsed = now - self._last_move_ts.get(self.room_name, now)
            self._last_move_ts[self.room_name] = now

            if current_turn == 'white':
                game.white_time_remaining = max(0, game.white_time_remaining - elapsed)
            else:
                game.black_time_remaining = max(0, game.black_time_remaining - elapsed)

            game.current_fen = new_fen
            await game.asave()

            # Check for timeout
            if game.white_time_remaining <= 0 or game.black_time_remaining <= 0:
                timeout_loser = 'white' if game.white_time_remaining <= 0 else 'black'
                timeout_winner = 'black' if timeout_loser == 'white' else 'white'
                game.status = Game.Status.RESIGNED
                game.winner = game.player_white if timeout_winner == 'white' else game.player_black
                await game.asave()
                await self._update_ratings(game, winner_color=timeout_winner)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_over',
                        'payload': {
                            'reason': 'timeout',
                            'winner': timeout_winner,
                            'loser': timeout_loser
                        }
                    }
                )
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_move',
                    'payload': {
                        'from_square': from_sq,
                        'to_square': to_sq,
                        'promotion': promotion,
                        'is_check': is_check,
                        'is_checkmate': is_checkmate,
                        'is_stalemate': is_stalemate,
                        'current_turn': self.board.current_turn,
                        'fen': new_fen,
                        'notation': notation,
                        'white_time': game.white_time_remaining,
                        'black_time': game.black_time_remaining,
                        'legal_moves': legal_moves
                    }
                }
            )

            await Move.objects.acreate(
                game=game,
                move_number=self.board.move_count,
                from_square=from_sq,
                to_square=to_sq,
                piece_moved=piece_name,
                piece_captured=captured_name,
                promotion=promotion,
                notation=notation,
                is_check=is_check,
                is_checkmate=is_checkmate,
                is_stalemate=is_stalemate,
                fen_after_move=new_fen,
            )

            if is_checkmate:
                game.status = Game.Status.CHECKMATE
                winner_color = 'white' if self.board.current_turn == 'black' else 'black'
                game.winner = game.player_white if winner_color == 'white' else game.player_black
                await game.asave()
                await self._update_ratings(game, winner_color=winner_color)
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_over',
                        'payload': {
                            'reason': 'checkmate', 
                            'winner': winner_color
                            }
                    }
                )
            elif is_stalemate:
                game.status = Game.Status.STALEMATE
                await game.asave()
                await self._update_ratings(game, is_draw=True)
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_over',
                        'payload': {
                            'reason': 'stalemate'
                            }
                    }
                )

        except Exception:
            logger.exception('Error processing move')

        if self.game_type == 'BOT' and game.status == Game.Status.IN_PROGRESS and not is_bot:
            await self._trigger_bot_move(game)

    async def _handle_resign(self):
        game = await self.get_game()
        if not game:
            return
            
        if game.status != Game.Status.IN_PROGRESS and game.status != Game.Status.WAITING:
            return

        if self.user_color == 'both':
            winner_color = 'black' if self.board.current_turn == 'white' else 'white'
        else:
            winner_color = 'black' if self.user_color == 'white' else 'white'

        game.status = Game.Status.RESIGNED
        if winner_color == 'white':
            game.winner = game.player_white
        else:
            game.winner = game.player_black
            
        await game.asave()
        await self._update_ratings(game, winner_color=winner_color)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_over',
                'payload': {
                    'reason': 'resign',
                    'winner': winner_color,
                    'resigned_by': self.user_color
                }
            }
        )

    async def _handle_offer_draw(self):
        """Handle a draw offer (online only)."""
        if self.game_type != 'ONLINE':
            await self.send_json({
                'type': 'error',
                'payload': {'message': 'Draw offers are only available in online games.'}
            })
            return

        game = await self.get_game()
        if not game or game.status != Game.Status.IN_PROGRESS:
            return

        # Prevent double-offering
        if self.room_name in self._draw_offered_by:
            await self.send_json({
                'type': 'error',
                'payload': {'message': 'A draw has already been offered. Wait for response.'}
            })
            return

        self._draw_offered_by[self.room_name] = self.user_color

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_draw_offer',
                'payload': {'offered_by': self.user_color}
            }
        )

    async def _handle_respond_draw(self, accepted: bool):
        """Handle response to a draw offer."""
        if self.room_name not in self._draw_offered_by:
            return

        offered_by = self._draw_offered_by.get(self.room_name)
        # Only the non-offering player can respond
        if self.user_color == offered_by:
            return

        self._draw_offered_by.pop(self.room_name, None)

        if accepted:
            game = await self.get_game()
            if not game or game.status != Game.Status.IN_PROGRESS:
                return
            game.status = Game.Status.DRAW
            await game.asave()
            await self._update_ratings(game, is_draw=True)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_over',
                    'payload': {'reason': 'draw', 'winner': ''}
                }
            )
        else:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_draw_declined',
                    'payload': {'declined_by': self.user_color}
                }
            )

    async def _handle_new_game(self):
        """Reset the board and start a new game in the same room."""
        self.active_boards[self.room_name] = Board()
        self.board = self.active_boards[self.room_name]
        self._draw_offered_by.pop(self.room_name, None)

        new_fen = self.board.get_fen()
        game = await self.get_game()
        if game:
            game.current_fen = new_fen
            game.status = Game.Status.IN_PROGRESS
            game.winner = None
            await game.asave()
            
        payload = {
            'type': 'game_state',
            'game_type': self.game_type,
            'payload': {
                'fen': new_fen,
                'current_turn': self.board.current_turn,
                'status': Game.Status.IN_PROGRESS,
            },
        }

        if getattr(self, 'game_type', None) == 'SOLO':
            await self.send_json(payload)
        else:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_new_game',
                    'payload': payload,
                },
            )

        logger.info('New game started in room %s', self.room_name)

    async def _trigger_bot_move(self, game):
        bot_action = await self.get_bot_move_async(game.bot_level, game.current_fen)
        
        if bot_action:
            await self._handle_move(bot_action, is_bot=True)

    @database_sync_to_async
    def get_bot_move_async(self, level, move_history):
        bot = ChessBot(level=level)
        return bot.get_best_move(move_history)

    async def _save_move_to_db(
        self,
        from_sq: str,
        to_sq: str,
        piece_name: str,
        captured_name: str,
        promotion: str,
        is_check: bool,
        is_checkmate: bool,
        is_stalemate: bool,
    ):
        try:
            game, _created = await Game.objects.aget_or_create(
                id=self.room_name if self.room_name.isdigit() else None,
                defaults={
                    'game_type': self.game_type,
                    'status': Game.Status.IN_PROGRESS,
                },
            )

            await Move.objects.acreate(
                game=game,
                move_number=self.board.move_count,
                from_square=from_sq,
                to_square=to_sq,
                piece_moved=piece_name,
                piece_captured=captured_name,
                promotion=promotion,
                is_check=is_check,
                is_checkmate=is_checkmate,
                is_stalemate=is_stalemate,
            )

            if is_checkmate:
                game.status = Game.Status.CHECKMATE
                game.winner = 'black' if self.board.current_turn == 'white' else 'white'
                await game.asave()
            elif is_stalemate:
                game.status = Game.Status.STALEMATE
                await game.asave()

        except Exception:
            logger.exception('Error saving move to DB')

    # --- Channel layer event handlers (for online mode) ---

    async def game_move(self, event):
        await self.send_json({
            'type': 'move_result',
            'payload': event['payload'],
        })

    async def game_over(self, event):
        await self.send_json({
            'type': 'game_over',
            'payload': event['payload'],
        })

    async def game_draw_offer(self, event):
        await self.send_json({
            'type': 'draw_offer',
            'payload': event['payload'],
        })

    async def game_draw_declined(self, event):
        await self.send_json({
            'type': 'draw_declined',
            'payload': event['payload'],
        })

    async def game_new_game(self, event):
        await self.send_json(event['payload'])