from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

from .views import GameViewSet, MoveViewSet, RegisterView, CurrentUserView, MatchmakingViewSet

router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')
router.register(r'moves', MoveViewSet, basename='move')
router.register(r'matchmaking', MatchmakingViewSet, basename='matchmaking')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', CurrentUserView.as_view(), name='profile'),
    path('', include(router.urls)),
]
