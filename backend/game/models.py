from django.db import models
from django.contrib.auth.models import User

class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player_profile')
    
    rating = models.IntegerField(default=500)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    
    bio = models.TextField(max_length=500, blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.rating})"

class MatchmakingQueue(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE)
    rating = models.IntegerField()
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ['joined_at']

    def __str__(self):
        return f"Searching: {self.player.user.username} (Rating: {self.rating})"

class Game(models.Model):
    class GameType(models.TextChoices):
        ONLINE = 'ONLINE', 'Online'
        SOLO = 'SOLO', 'Play vs Yourself'
        BOT = 'BOT', 'Play vs Bot'

    class Status(models.TextChoices):
        WAITING = 'WAITING', 'Waiting for Player'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        CHECKMATE = 'CHECKMATE', 'Checkmate'
        STALEMATE = 'STALEMATE', 'Stalemate'
        DRAW = 'DRAW', 'Draw'
        RESIGNED = 'RESIGNED', 'Resigned'

    game_type = models.CharField(
        max_length=10,
        choices=GameType.choices,
        default=GameType.ONLINE,
    )

    player_white = models.ForeignKey(Player, related_name='games_as_white', on_delete=models.SET_NULL, null=True, blank=True)
    player_black = models.ForeignKey(Player, related_name='games_as_black', on_delete=models.SET_NULL, null=True, blank=True)

    bot_level  = models.IntegerField(null=True, blank=True)

    STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    current_fen = models.CharField(max_length=100, default=STARTING_FEN)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
    )
    winner = models.ForeignKey(Player, related_name='won_games', on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_move_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'[{self.game_type}] {self.player_white} vs {self.player_black}'


class Move(models.Model):
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