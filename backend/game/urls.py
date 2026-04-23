from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

from .views import GameViewSet, MoveViewSet, RegisterView, CurrentUserView, MatchmakingViewSet, UpdateAvatarView, UpdateUsernameView

router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')
router.register(r'moves', MoveViewSet, basename='move')
router.register(r'matchmaking', MatchmakingViewSet, basename='matchmaking')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', CurrentUserView.as_view(), name='profile'),
    path('profile/avatar/', UpdateAvatarView.as_view(), name='update_avatar'),
    path('profile/username/', UpdateUsernameView.as_view(), name='update_username'),
    path('', include(router.urls)),
]

# =====================================================================
# Alternative FBV routes (Function-Based Views using @api_view)
# =====================================================================
# from .views.fbv_views import (
#     register_user, get_profile, list_create_games, game_detail,
#     game_moves, join_matchmaking, leave_matchmaking,
#     update_avatar as fbv_update_avatar,
#     update_username as fbv_update_username,
# )
#
# urlpatterns += [
#     path('fbv/register/', register_user, name='fbv-register'),
#     path('fbv/profile/', get_profile, name='fbv-profile'),
#     path('fbv/profile/avatar/', fbv_update_avatar, name='fbv-update-avatar'),
#     path('fbv/profile/username/', fbv_update_username, name='fbv-update-username'),
#     path('fbv/games/', list_create_games, name='fbv-games'),
#     path('fbv/games/<int:pk>/', game_detail, name='fbv-game-detail'),
#     path('fbv/games/<int:pk>/moves/', game_moves, name='fbv-game-moves'),
#     path('fbv/matchmaking/join/', join_matchmaking, name='fbv-matchmaking-join'),
#     path('fbv/matchmaking/leave/', leave_matchmaking, name='fbv-matchmaking-leave'),
# ]

# =====================================================================
# Alternative CBV routes (Class-Based Views using APIView)
# =====================================================================
# from .views.cbv_views import (
#     RegisterAPIView, ProfileAPIView, GameListAPIView, GameDetailAPIView,
#     GameMovesAPIView, MatchmakingJoinAPIView, MatchmakingLeaveAPIView,
#     AvatarAPIView, UsernameAPIView,
# )
#
# urlpatterns += [
#     path('cbv/register/', RegisterAPIView.as_view(), name='cbv-register'),
#     path('cbv/profile/', ProfileAPIView.as_view(), name='cbv-profile'),
#     path('cbv/profile/avatar/', AvatarAPIView.as_view(), name='cbv-update-avatar'),
#     path('cbv/profile/username/', UsernameAPIView.as_view(), name='cbv-update-username'),
#     path('cbv/games/', GameListAPIView.as_view(), name='cbv-games'),
#     path('cbv/games/<int:pk>/', GameDetailAPIView.as_view(), name='cbv-game-detail'),
#     path('cbv/games/<int:pk>/moves/', GameMovesAPIView.as_view(), name='cbv-game-moves'),
#     path('cbv/matchmaking/join/', MatchmakingJoinAPIView.as_view(), name='cbv-matchmaking-join'),
#     path('cbv/matchmaking/leave/', MatchmakingLeaveAPIView.as_view(), name='cbv-matchmaking-leave'),
# ]
