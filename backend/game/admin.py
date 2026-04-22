from django.contrib import admin
from .models import Game, Player, MatchmakingQueue, User, Move

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'wins', 'losses', 'created_at')
    search_fields = ('user__username', 'user__email')
    list_filter = ('created_at',)

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'game_type', 'status', 'player_white', 'player_black', 'winner', 'created_at')
    list_filter = ('game_type', 'status', 'created_at')
    ordering = ('-created_at',)
    search_fields = ('player_white__user__username', 'player_black__user__username')

@admin.register(Move)
class MoveAdmin(admin.ModelAdmin):
    list_display = ('game', 'move_number', 'piece_moved', 'from_square', 'to_square', 'timestamp')
    list_filter = ('piece_moved', 'is_checkmate')

@admin.register(MatchmakingQueue)
class MatchmakingAdmin(admin.ModelAdmin):
    list_display = ('player', 'rating', 'joined_at')