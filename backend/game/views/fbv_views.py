"""
Function-Based Views (FBV) с использованием DRF декораторов.

Альтернативная реализация всех API эндпоинтов через @api_view.
Эти views НЕ подключены к urls.py — используются только как пример.
"""

import random
from django.db.models import Q
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..models import Game, Move, MatchmakingQueue, Player
from ..serializers import (
    GameSerializer, MoveSerializer, RegisterSerializer, UserSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """POST /api/fbv/register/ — Регистрация нового пользователя."""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """GET /api/fbv/profile/ — Получение профиля текущего пользователя."""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_create_games(request):
    """
    GET  /api/fbv/games/ — Список игр с фильтрацией.
    POST /api/fbv/games/ — Создание новой игры.
    """
    if request.method == 'GET':
        queryset = Game.objects.all().order_by('-created_at').select_related(
            'player_white__user', 'player_black__user', 'winner__user'
        )

        game_status = request.query_params.get('status')
        if game_status:
            queryset = queryset.filter(status=game_status)

        game_type = request.query_params.get('type')
        if game_type:
            queryset = queryset.filter(game_type=game_type.upper())

        mine = request.query_params.get('mine')
        if mine:
            player = request.user.player_profile
            queryset = queryset.filter(
                Q(player_white=player) | Q(player_black=player)
            )

        serializer = GameSerializer(queryset, many=True)
        return Response(serializer.data)

    # POST — создание игры
    player = request.user.player_profile
    game_type = request.data.get('game_type', Game.GameType.SOLO)
    bot_level = request.data.get('bot_level')
    requested_side = request.data.get('side', 'white')
    time_control = int(request.data.get('time_control', 15))
    time_seconds = time_control * 60

    if requested_side == 'random':
        actual_side = random.choice(['white', 'black'])
    else:
        actual_side = requested_side

    if actual_side == 'white':
        p_white, p_black = player, None
    else:
        p_white, p_black = None, player

    new_game = Game.objects.create(
        game_type=game_type,
        player_white=p_white,
        player_black=p_black,
        bot_level=bot_level if game_type == Game.GameType.BOT else None,
        time_control=time_control,
        white_time_remaining=time_seconds,
        black_time_remaining=time_seconds,
        status=Game.Status.IN_PROGRESS,
    )
    serializer = GameSerializer(new_game)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def game_detail(request, pk):
    """GET /api/fbv/games/<pk>/ — Детали конкретной игры."""
    try:
        game = Game.objects.select_related(
            'player_white__user', 'player_black__user', 'winner__user'
        ).get(pk=pk)
    except Game.DoesNotExist:
        return Response(
            {"error": "Game not found"}, status=status.HTTP_404_NOT_FOUND
        )
    serializer = GameSerializer(game)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def game_moves(request, pk):
    """GET /api/fbv/games/<pk>/moves/ — Ходы конкретной игры."""
    try:
        game = Game.objects.get(pk=pk)
    except Game.DoesNotExist:
        return Response(
            {"error": "Game not found"}, status=status.HTTP_404_NOT_FOUND
        )
    moves = game.moves.all().order_by('move_number')
    serializer = MoveSerializer(moves, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_matchmaking(request):
    """POST /api/fbv/matchmaking/join/ — Присоединиться к очереди поиска."""
    player = request.user.player_profile

    active_online = Game.objects.filter(
        Q(player_white=player) | Q(player_black=player),
        status=Game.Status.IN_PROGRESS,
        game_type=Game.GameType.ONLINE,
    ).order_by('-created_at').first()

    if active_online:
        return Response(
            {"status": "game_found", "game_id": active_online.id},
            status=status.HTTP_200_OK,
        )

    rating_range = 100
    opponent_entry = (
        MatchmakingQueue.objects.filter(
            rating__gte=player.rating - rating_range,
            rating__lte=player.rating + rating_range,
        )
        .exclude(player=player)
        .first()
    )

    if opponent_entry:
        opponent = opponent_entry.player
        players = [player, opponent]
        random.shuffle(players)
        time_seconds = 15 * 60
        with transaction.atomic():
            opponent_entry.delete()
            MatchmakingQueue.objects.filter(player=player).delete()
            new_game = Game.objects.create(
                game_type=Game.GameType.ONLINE,
                player_white=players[0],
                player_black=players[1],
                time_control=15,
                white_time_remaining=time_seconds,
                black_time_remaining=time_seconds,
                status=Game.Status.IN_PROGRESS,
            )
        return Response(
            {"status": "game_found", "game_id": new_game.id},
            status=status.HTTP_201_CREATED,
        )

    MatchmakingQueue.objects.update_or_create(
        player=player, defaults={"rating": player.rating}
    )
    return Response({"status": "searching"}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def leave_matchmaking(request):
    """DELETE /api/fbv/matchmaking/leave/ — Покинуть очередь поиска."""
    MatchmakingQueue.objects.filter(
        player=request.user.player_profile
    ).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def update_avatar(request):
    """
    PATCH  /api/fbv/profile/avatar/ — Загрузить аватар.
    DELETE /api/fbv/profile/avatar/ — Удалить аватар.
    """
    player = request.user.player_profile

    if request.method == 'PATCH':
        avatar = request.FILES.get('avatar')
        if not avatar:
            return Response(
                {"error": "No avatar file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        player.avatar = avatar
        player.save()
        return Response({"avatar": player.avatar.url if player.avatar else None})

    # DELETE
    if player.avatar:
        player.avatar.delete(save=False)
        player.avatar = None
        player.save()
    return Response({"avatar": None})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_username(request):
    """PATCH /api/fbv/profile/username/ — Обновить имя пользователя."""
    new_username = request.data.get('username', '').strip()
    if not new_username:
        return Response(
            {"error": "Username is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(new_username) < 3:
        return Response(
            {"error": "Username must be at least 3 characters"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if (
        User.objects.filter(username=new_username)
        .exclude(pk=request.user.pk)
        .exists()
    ):
        return Response(
            {"error": "Username already taken"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    request.user.username = new_username
    request.user.save()
    return Response({"username": new_username})
