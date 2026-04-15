from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Game, Move
from .serializers import GameSerializer, MoveSerializer


class GameViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для шахматных партий.

    GET  /api/games/              — список всех игр (фильтрация: ?status=IN_PROGRESS&type=SOLO)
    GET  /api/games/<id>/         — детали конкретной игры (включая все ходы)
    GET  /api/games/<id>/moves/   — список ходов конкретной игры
    POST /api/games/              — создание новой игры
    """
    queryset = Game.objects.all().order_by('-created_at')
    serializer_class = GameSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status: ?status=IN_PROGRESS
        game_status = self.request.query_params.get('status')
        if game_status:
            queryset = queryset.filter(status=game_status)

        # Filter by type: ?type=SOLO
        game_type = self.request.query_params.get('type')
        if game_type:
            queryset = queryset.filter(game_type=game_type.upper())

        return queryset

    def create(self, request, *args, **kwargs):
        """POST /api/games/ — создание новой игры."""
        game_type = request.data.get('game_type', 'SOLO')
        game = Game.objects.create(
            game_type=game_type,
            status=Game.Status.IN_PROGRESS,
        )
        serializer = self.get_serializer(game)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def moves(self, request, pk=None):
        """GET /api/games/<id>/moves/ — история ходов."""
        game = self.get_object()
        moves = game.moves.all().order_by('move_number')
        serializer = MoveSerializer(moves, many=True)
        return Response(serializer.data)


class MoveViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для ходов (только чтение).

    GET /api/moves/       — все ходы
    GET /api/moves/<id>/  — конкретный ход
    """
    queryset = Move.objects.all().order_by('-timestamp')
    serializer_class = MoveSerializer
