import logging
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
            self.active_boards[self.room_name] = Board()
        self.board = self.active_boards[self.room_name]

        await self.accept()
        
        await self.send_json({
            'type': 'connection_established',
            'color': self.user_color,
            'game_type': self.game_type
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
                    },
                })
            case _:
                await self.send_json({
                    'type': 'error',
                    'payload': {
                        'message': f'Unknown action: {action}',
                        'valid_actions': ['move', 'resign', 'get_state', 'new_game'],
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
            game.current_fen = new_fen
            await game.asave()
            is_check = self.board.is_in_check(self.board.current_turn)
            is_checkmate = self.board.is_checkmate(self.board.current_turn)
            is_stalemate = self.board.is_stalemate(self.board.current_turn)

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

    async def _handle_new_game(self):
        """Reset the board and start a new game in the same room."""
        self.active_boards[self.room_name] = Board()
        self.board = self.active_boards[self.room_name]

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

    async def game_new_game(self, event):
        await self.send_json(event['payload'])