# Re-export all views from views_original so existing imports keep working
from .views_original import (
    has_active_game,
    GameViewSet,
    MoveViewSet,
    RegisterView,
    CurrentUserView,
    UpdateAvatarView,
    UpdateUsernameView,
    MatchmakingViewSet,
)

__all__ = [
    'has_active_game',
    'GameViewSet',
    'MoveViewSet',
    'RegisterView',
    'CurrentUserView',
    'UpdateAvatarView',
    'UpdateUsernameView',
    'MatchmakingViewSet',
]
