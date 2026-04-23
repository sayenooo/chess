import random
from django.db.models import Q
from rest_framework import viewsets, status, generics, permissions
from django.contrib.auth.models import User
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Game, Move, MatchmakingQueue
from .serializers import GameSerializer, MoveSerializer, RegisterSerializer, UserSerializer

def has_active_game(player):
    return Game.objects.filter(
        Q(player_white=player) | Q(player_black=player),
        status=Game.Status.IN_PROGRESS
    ).exists()

class GameViewSet(viewsets.ModelViewSet):
    """
    API для шахматных партий.

    GET  /api/games/              — список всех игр (фильтрация: ?status=IN_PROGRESS&type=SOLO)
    GET  /api/games/<id>/         — детали конкретной игры (включая все ходы)
    GET  /api/games/<id>/moves/   — список ходов конкретной игры
    POST /api/games/              — создание новой игры
    """
    queryset = Game.objects.all().order_by('-created_at').select_related(
        'player_white__user', 'player_black__user', 'winner__user'
    )
    serializer_class = GameSerializer
    permission_classes = (permissions.IsAuthenticated,)

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

        # Filter by current user: ?mine=true
        mine = self.request.query_params.get('mine')
        if mine:
            player = self.request.user.player_profile
            queryset = queryset.filter(Q(player_white=player) | Q(player_black=player))

        return queryset

    def create(self, request, *args, **kwargs):
        """POST /api/games/ — creating a new game (SOLO or BOT)."""
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
            status=Game.Status.IN_PROGRESS
        )
        serializer = self.get_serializer(new_game)
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

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

class UpdateAvatarView(generics.UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, *args, **kwargs):
        player = request.user.player_profile
        avatar = request.FILES.get('avatar')
        if not avatar:
            return Response({"error": "No avatar file provided"}, status=status.HTTP_400_BAD_REQUEST)
        player.avatar = avatar
        player.save()
        return Response({"avatar": player.avatar.url if player.avatar else None})

    def delete(self, request, *args, **kwargs):
        player = request.user.player_profile
        if player.avatar:
            player.avatar.delete(save=False)
            player.avatar = None
            player.save()
        return Response({"avatar": None})

class UpdateUsernameView(generics.UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, *args, **kwargs):
        new_username = request.data.get('username', '').strip()
        if not new_username:
            return Response({"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_username) < 3:
            return Response({"error": "Username must be at least 3 characters"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=new_username).exclude(pk=request.user.pk).exists():
            return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.username = new_username
        request.user.save()
        return Response({"username": new_username})
    
class MatchmakingViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    # POST /api/matchmaking/join/
    @action(detail=False, methods=['post'])
    def join(self, request):
        player = request.user.player_profile
        
        # Only check for active ONLINE games (not SOLO/BOT)
        active_online = Game.objects.filter(
            Q(player_white=player) | Q(player_black=player),
            status=Game.Status.IN_PROGRESS,
            game_type=Game.GameType.ONLINE
        ).order_by('-created_at').first()
        
        if active_online:
            return Response({
                "status": "game_found",
                "game_id": active_online.id
            }, status=status.HTTP_200_OK)
        
        rating_range = 100
        opponent_entry = MatchmakingQueue.objects.filter(
            rating__gte=player.rating - rating_range,
            rating__lte=player.rating + rating_range
        ).exclude(player=player).first()

        if opponent_entry:
            opponent = opponent_entry.player
            players = [player, opponent]
            random.shuffle(players)
            time_seconds = 15 * 60
            with transaction.atomic():
                opponent_entry.delete()
                # Also clean up our own queue entry if present
                MatchmakingQueue.objects.filter(player=player).delete()
                new_game = Game.objects.create(
                    game_type=Game.GameType.ONLINE,
                    player_white=players[0],
                    player_black=players[1],
                    time_control=15,
                    white_time_remaining=time_seconds,
                    black_time_remaining=time_seconds,
                    status=Game.Status.IN_PROGRESS
                )
            return Response({
                "status": "game_found",
                "game_id": new_game.id
            }, status=status.HTTP_201_CREATED)
        
        MatchmakingQueue.objects.update_or_create(
            player=player,
            defaults={'rating': player.rating}
        )
        return Response({"status": "searching"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['delete'])
    def leave(self, request):
        MatchmakingQueue.objects.filter(player=request.user.player_profile).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
