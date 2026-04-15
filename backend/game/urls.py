from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import GameViewSet, MoveViewSet

router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')
router.register(r'moves', MoveViewSet, basename='move')

urlpatterns = [
    path('', include(router.urls)),
]
