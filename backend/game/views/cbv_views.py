"""
Class-Based Views (CBV) с использованием APIView.
Альтернативная реализация API. НЕ подключены к urls.py.
"""
import random
from django.db.models import Q
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from ..models import Game, Move, MatchmakingQueue
from ..serializers import GameSerializer, MoveSerializer, RegisterSerializer, UserSerializer


class RegisterAPIView(APIView):
    """POST — Регистрация нового пользователя."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileAPIView(APIView):
    """GET — Профиль текущего пользователя."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class GameListAPIView(APIView):
    """GET/POST — Список игр и создание новой."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Game.objects.all().order_by('-created_at').select_related(
            'player_white__user', 'player_black__user', 'winner__user'
        )
        s = request.query_params.get('status')
        if s:
            qs = qs.filter(status=s)
        t = request.query_params.get('type')
        if t:
            qs = qs.filter(game_type=t.upper())
        if request.query_params.get('mine'):
            p = request.user.player_profile
            qs = qs.filter(Q(player_white=p) | Q(player_black=p))
        return Response(GameSerializer(qs, many=True).data)

    def post(self, request):
        player = request.user.player_profile
        gt = request.data.get('game_type', Game.GameType.SOLO)
        side = request.data.get('side', 'white')
        tc = int(request.data.get('time_control', 15))
        actual = random.choice(['white', 'black']) if side == 'random' else side
        pw, pb = (player, None) if actual == 'white' else (None, player)
        game = Game.objects.create(
            game_type=gt, player_white=pw, player_black=pb,
            bot_level=request.data.get('bot_level') if gt == Game.GameType.BOT else None,
            time_control=tc, white_time_remaining=tc*60, black_time_remaining=tc*60,
            status=Game.Status.IN_PROGRESS,
        )
        return Response(GameSerializer(game).data, status=status.HTTP_201_CREATED)


class GameDetailAPIView(APIView):
    """GET — Детали конкретной игры."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            game = Game.objects.select_related(
                'player_white__user', 'player_black__user', 'winner__user'
            ).get(pk=pk)
        except Game.DoesNotExist:
            return Response({"error": "Game not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(GameSerializer(game).data)


class GameMovesAPIView(APIView):
    """GET — Ходы конкретной игры."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            game = Game.objects.get(pk=pk)
        except Game.DoesNotExist:
            return Response({"error": "Game not found"}, status=status.HTTP_404_NOT_FOUND)
        moves = game.moves.all().order_by('move_number')
        return Response(MoveSerializer(moves, many=True).data)


class MatchmakingJoinAPIView(APIView):
    """POST — Присоединиться к очереди поиска."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        player = request.user.player_profile
        active = Game.objects.filter(
            Q(player_white=player) | Q(player_black=player),
            status=Game.Status.IN_PROGRESS, game_type=Game.GameType.ONLINE,
        ).order_by('-created_at').first()
        if active:
            return Response({"status": "game_found", "game_id": active.id})
        opp = MatchmakingQueue.objects.filter(
            rating__gte=player.rating - 100, rating__lte=player.rating + 100,
        ).exclude(player=player).first()
        if opp:
            players = [player, opp.player]
            random.shuffle(players)
            with transaction.atomic():
                opp.delete()
                MatchmakingQueue.objects.filter(player=player).delete()
                game = Game.objects.create(
                    game_type=Game.GameType.ONLINE,
                    player_white=players[0], player_black=players[1],
                    time_control=15, white_time_remaining=900, black_time_remaining=900,
                    status=Game.Status.IN_PROGRESS,
                )
            return Response({"status": "game_found", "game_id": game.id}, status=status.HTTP_201_CREATED)
        MatchmakingQueue.objects.update_or_create(player=player, defaults={"rating": player.rating})
        return Response({"status": "searching"})


class MatchmakingLeaveAPIView(APIView):
    """DELETE — Покинуть очередь поиска."""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        MatchmakingQueue.objects.filter(player=request.user.player_profile).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AvatarAPIView(APIView):
    """PATCH/DELETE — Загрузить или удалить аватар."""
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        player = request.user.player_profile
        avatar = request.FILES.get('avatar')
        if not avatar:
            return Response({"error": "No avatar file provided"}, status=status.HTTP_400_BAD_REQUEST)
        player.avatar = avatar
        player.save()
        return Response({"avatar": player.avatar.url if player.avatar else None})

    def delete(self, request):
        player = request.user.player_profile
        if player.avatar:
            player.avatar.delete(save=False)
            player.avatar = None
            player.save()
        return Response({"avatar": None})


class UsernameAPIView(APIView):
    """PATCH — Обновить имя пользователя."""
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        name = request.data.get('username', '').strip()
        if not name:
            return Response({"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)
        if len(name) < 3:
            return Response({"error": "Username must be at least 3 characters"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=name).exclude(pk=request.user.pk).exists():
            return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.username = name
        request.user.save()
        return Response({"username": name})
