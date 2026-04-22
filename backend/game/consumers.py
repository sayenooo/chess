import logging
from typing import ClassVar
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncJsonWebsocketConsumer

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
        self.room_name: str = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'

        # Determine game type from query string: ?type=solo|online|bot
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        params = parse_qs(query_string)
        type_param = params.get('type', ['online'])[0].upper()
        self.game_type = type_param if type_param in ('SOLO', 'ONLINE', 'BOT') else 'ONLINE'
        self.is_solo = self.game_type == 'SOLO'

        # Create a new board for this room if it doesn't exist yet
        if self.room_name not in self.active_boards:
            self.active_boards[self.room_name] = Board()

        self.board = self.active_boards[self.room_name]

        # For online mode — join the channel group for broadcasting
        if not self.is_solo:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name,
            )

        await self.accept()

        logger.info(
            'Player connected to room %s (type=%s)',
            self.room_group_name,
            self.game_type,
        )

        # Send initial game state
        await self.send_json({
            'type': 'game_state',
            'game_type': self.game_type,
            'payload': self.board.to_dict(),
        })

    async def disconnect(self, close_code):
        if not self.is_solo:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

        # Clean up board when everyone disconnects (solo always cleans up)
        if self.is_solo:
            self.active_boards.pop(self.room_name, None)

        logger.info('Player disconnected from room %s', self.room_group_name)

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
                await self.send_json({
                    'type': 'game_state',
                    'game_type': self.game_type,
                    'payload': self.board.to_dict(),
                })
            case _:
                await self.send_json({
                    'type': 'error',
                    'payload': {
                        'message': f'Unknown action: {action}',
                        'valid_actions': ['move', 'resign', 'get_state', 'new_game'],
                    },
                })

    async def _handle_move(self, content: dict):
        # 1. Validate input data using MoveInputSerializer
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

        data = serializer.validated_data
        from_sq = data['from_square']
        to_sq = data['to_square']
        promotion = data.get('promotion', 'Queen')

        # 2. Parse square notation
        start_row, start_col = parse_square(from_sq)
        end_row, end_col = parse_square(to_sq)

        # 3. Check if there is a piece on the from_square and if it belongs to the current player
        piece = self.board.get_piece_at(start_row, start_col)
        if piece is None:
            await self.send_json({
                'type': 'error',
                'payload': {'message': f'There is no piece on {from_sq}'},
            })
            return

        if piece.color != self.board.current_turn:
            await self.send_json({
                'type': 'error',
                'payload': {'message': f'Currently it is {self.board.current_turn}\'s turn, but the piece on {from_sq} is {piece.color}'},
            })
            return

        # 4. Check if the move is legal for this piece
        legal_moves = piece.get_legal_moves(self.board)
        if (end_row, end_col) not in legal_moves:
            await self.send_json({
                'type': 'error',
                'payload': {
                    'message': f'Illegal move: {from_sq} → {to_sq}',
                    'legal_moves': [format_square(r, c) for r, c in legal_moves],
                },
            })
            return

        # 5. Make the move on the board
        piece_name = piece.__class__.__name__
        captured = self.board.move_piece(
            (start_row, start_col),
            (end_row, end_col),
            promotion_choice=promotion,
        )

        # 6. Check / Checkmate / Stalemate
        opponent = self.board.current_turn
        is_check = self.board.is_in_check(opponent)
        is_checkmate = self.board.is_checkmate(opponent)
        is_stalemate = self.board.is_stalemate(opponent)

        status = 'in_progress'
        if is_checkmate:
            status = 'checkmate'
        elif is_stalemate:
            status = 'stalemate'
        elif is_check:
            status = 'check'

        # 7. Format move result
        move_result = {
            'from_square': from_sq,
            'to_square': to_sq,
            'piece': piece_name,
            'captured': captured.__class__.__name__ if captured else None,
            'promotion': promotion if piece_name == 'Pawn' and (end_row == 0 or end_row == 7) else None,
            'is_check': is_check,
            'is_checkmate': is_checkmate,
            'is_stalemate': is_stalemate,
            'status': status,
            'board': self.board.to_dict(),
        }

        # 8. Send result — solo sends directly, online broadcasts to group
        if self.is_solo:
            await self.send_json({
                'type': 'move_result',
                'payload': move_result,
            })
        else:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game.move',
                    'payload': move_result,
                },
            )

        # 9. Save move to DB
        await self._save_move_to_db(
            from_sq=from_sq,
            to_sq=to_sq,
            piece_name=piece_name,
            captured_name=captured.__class__.__name__ if captured else '',
            promotion=promotion if piece_name == 'Pawn' and (end_row == 0 or end_row == 7) else '',
            is_check=is_check,
            is_checkmate=is_checkmate,
            is_stalemate=is_stalemate,
        )

    async def _handle_resign(self):
        payload = {
            'reason': 'resign',
            'message': 'Player has resigned. Game over.',
        }

        if self.is_solo:
            await self.send_json({
                'type': 'game_over',
                'payload': payload,
            })
        else:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game.over',
                    'payload': payload,
                },
            )

    async def _handle_new_game(self):
        """Reset the board and start a new game in the same room."""
        self.active_boards[self.room_name] = Board()
        self.board = self.active_boards[self.room_name]

        payload = {
            'type': 'game_state',
            'game_type': self.game_type,
            'payload': self.board.to_dict(),
        }

        if self.is_solo:
            await self.send_json(payload)
        else:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game.new_game',
                    'payload': payload,
                },
            )

        logger.info('New game started in room %s', self.room_name)

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