import logging
from typing import ClassVar

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from game.engine.board import Board, parse_square, format_square
from game.models import Game, Move
from game.serializers import MoveInputSerializer

logger = logging.getLogger(__name__)


class ChessConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer для шахматной партии.

    Жизненный цикл:
    ────────────────
    1. connect()    — клиент подключается к комнате, получает начальное состояние
    2. receive_json — клиент шлёт action ('move' / 'resign' / 'get_state')
    3. disconnect() — клиент отключается

    Почему async?
    ─────────────
    Все методы `async`, потому что Django Channels работает асинхронно.
    `await` освобождает поток, пока ждём ответ от БД / Redis,
    позволяя серверу параллельно обслуживать других игроков.
    """

    # ── Общий словарь: room_name → Board (одна доска на комнату) ──
    active_boards: ClassVar[dict[str, Board]] = {}

    # ─────────────────────────────────────────────
    # ПОДКЛЮЧЕНИЕ
    # ─────────────────────────────────────────────
    async def connect(self):
        self.room_name: str = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'

        # Создаём Board, если комнаты ещё нет
        if self.room_name not in self.active_boards:
            self.active_boards[self.room_name] = Board()

        self.board = self.active_boards[self.room_name]

        # Подключаемся к группе (Redis / InMemory channel layer)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

        logger.info('Игрок подключился к комнате %s', self.room_group_name)

        # Отправляем начальное состояние доски **только этому** клиенту
        await self.send_json({
            'type': 'game_state',
            'payload': self.board.to_dict(),
        })

    # ─────────────────────────────────────────────
    # ОТКЛЮЧЕНИЕ
    # ─────────────────────────────────────────────
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )
        logger.info('Игрок покинул комнату %s', self.room_group_name)

    # ─────────────────────────────────────────────
    # ПОЛУЧЕНИЕ СООБЩЕНИЯ ОТ КЛИЕНТА
    # ─────────────────────────────────────────────
    async def receive_json(self, content: dict):
        """
        Обрабатывает JSON от фронтенда.

        Формат входящего сообщения:
        {
            "action": "move" | "resign" | "get_state",
            "from_square": "e2",     // только для move
            "to_square": "e4",       // только для move
            "promotion": "Queen"     // опционально, только для move
        }
        """
        action = content.get('action')

        match action:
            case 'move':
                await self._handle_move(content)
            case 'resign':
                await self._handle_resign()
            case 'get_state':
                await self.send_json({
                    'type': 'game_state',
                    'payload': self.board.to_dict(),
                })
            case _:
                await self.send_json({
                    'type': 'error',
                    'payload': {
                        'message': f'Неизвестное действие: {action}',
                        'valid_actions': ['move', 'resign', 'get_state'],
                    },
                })

    # ─────────────────────────────────────────────
    # ОБРАБОТКА ХОДА
    # ─────────────────────────────────────────────
    async def _handle_move(self, content: dict):
        # 1. Валидация формата через сериализатор
        serializer = MoveInputSerializer(data=content)
        if not serializer.is_valid():
            await self.send_json({
                'type': 'error',
                'payload': {
                    'message': 'Неверный формат хода',
                    'details': serializer.errors,
                },
            })
            return

        data = serializer.validated_data
        from_sq = data['from_square']
        to_sq = data['to_square']
        promotion = data.get('promotion', 'Queen')

        # 2. Парсим координаты
        start_row, start_col = parse_square(from_sq)
        end_row, end_col = parse_square(to_sq)

        # 3. Проверяем, есть ли фигура и того ли цвета
        piece = self.board.get_piece_at(start_row, start_col)
        if piece is None:
            await self.send_json({
                'type': 'error',
                'payload': {'message': f'Нет фигуры на {from_sq}'},
            })
            return

        if piece.color != self.board.current_turn:
            await self.send_json({
                'type': 'error',
                'payload': {'message': f'Сейчас ход {self.board.current_turn}, а фигура на {from_sq} — {piece.color}'},
            })
            return

        # 4. Проверяем легальность хода
        legal_moves = piece.get_legal_moves(self.board)
        if (end_row, end_col) not in legal_moves:
            await self.send_json({
                'type': 'error',
                'payload': {
                    'message': f'Нелегальный ход: {from_sq} → {to_sq}',
                    'legal_moves': [format_square(r, c) for r, c in legal_moves],
                },
            })
            return

        # 5. Выполняем ход
        piece_name = piece.__class__.__name__
        captured = self.board.move_piece(
            (start_row, start_col),
            (end_row, end_col),
            promotion_choice=promotion,
        )

        # 6. Проверяем статус игры после хода
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

        # 7. Формируем ответ и рассылаем всем в комнате
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

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game.move',
                'payload': move_result,
            },
        )

        # 8. Сохраняем ход в БД (async ORM — Django 6)
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

    # ─────────────────────────────────────────────
    # СДАЧА
    # ─────────────────────────────────────────────
    async def _handle_resign(self):
        # TODO: определять, кто именно сдался (по цвету)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game.over',
                'payload': {
                    'reason': 'resign',
                    'message': 'Игрок сдался',
                },
            },
        )

    # ─────────────────────────────────────────────
    # СОХРАНЕНИЕ В БД (async ORM)
    # ─────────────────────────────────────────────
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
        """
        Сохраняет ход асинхронно.

        Почему await + acreate / aget_or_create?
        ─────────────────────────────────────────
        Django 6 поддерживает async ORM. Вместо синхронных
        Game.objects.get() мы используем Game.objects.aget(),
        чтобы не блокировать event loop WebSocket-сервера.
        """
        try:
            # Получаем или создаём запись Game для этой комнаты
            game, _created = await Game.objects.aget_or_create(
                id=self.room_name if self.room_name.isdigit() else None,
                defaults={
                    'game_type': Game.GameType.ONLINE,
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

            # Обновляем статус игры если мат/пат
            if is_checkmate:
                game.status = Game.Status.CHECKMATE
                # Победитель — тот, кто сделал этот ход (противник текущего хода)
                game.winner = 'black' if self.board.current_turn == 'white' else 'white'
                await game.asave()
            elif is_stalemate:
                game.status = Game.Status.STALEMATE
                await game.asave()

        except Exception:
            logger.exception('Ошибка при сохранении хода в БД')

    # ─────────────────────────────────────────────
    # ОБРАБОТЧИКИ GROUP_SEND (названия через точку)
    # ─────────────────────────────────────────────
    async def game_move(self, event):
        """Рассылает результат хода всем в комнате."""
        await self.send_json({
            'type': 'move_result',
            'payload': event['payload'],
        })

    async def game_over(self, event):
        """Рассылает окончание игры всем в комнате."""
        await self.send_json({
            'type': 'game_over',
            'payload': event['payload'],
        })