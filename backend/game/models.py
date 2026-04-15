from django.db import models


class Game(models.Model):
    """Модель шахматной партии — поддерживает ONLINE / SOLO / BOT."""

    class GameType(models.TextChoices):
        ONLINE = 'ONLINE', 'Онлайн'
        SOLO = 'SOLO', 'С самим собой'
        BOT = 'BOT', 'Против бота'

    class Status(models.TextChoices):
        WAITING = 'WAITING', 'Ожидание игрока'
        IN_PROGRESS = 'IN_PROGRESS', 'В процессе'
        CHECKMATE = 'CHECKMATE', 'Мат'
        STALEMATE = 'STALEMATE', 'Пат'
        DRAW = 'DRAW', 'Ничья'
        RESIGNED = 'RESIGNED', 'Сдача'

    # --- Тип режима ---
    game_type = models.CharField(
        max_length=10,
        choices=GameType.choices,
        default=GameType.ONLINE,
    )

    # --- Игроки (blank/null для SOLO и BOT) ---
    player_white = models.CharField(max_length=100, blank=True, default='')
    player_black = models.CharField(max_length=100, blank=True, default='')

    # --- Состояние ---
    STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    current_fen = models.CharField(max_length=100, default=STARTING_FEN)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
    )
    winner = models.CharField(max_length=10, blank=True, default='')

    # --- Временные метки ---
    created_at = models.DateTimeField(auto_now_add=True)
    last_move_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'[{self.game_type}] {self.player_white} vs {self.player_black}'


class Move(models.Model):
    """Один ход в партии."""

    game = models.ForeignKey(Game, related_name='moves', on_delete=models.CASCADE)
    move_number = models.IntegerField()
    from_square = models.CharField(max_length=2)
    to_square = models.CharField(max_length=2)
    piece_moved = models.CharField(max_length=20)
    piece_captured = models.CharField(max_length=20, blank=True, default='')
    promotion = models.CharField(max_length=10, blank=True, default='')
    notation = models.CharField(max_length=10, blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_check = models.BooleanField(default=False)
    is_checkmate = models.BooleanField(default=False)
    is_stalemate = models.BooleanField(default=False)