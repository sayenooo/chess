from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Game, Move, Player, MatchmakingQueue

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['rating', 'bio', 'created_at', 'wins', 'losses', 'draws', 'avatar']

class UserSerializer(serializers.ModelSerializer):
    player_profile = PlayerSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'player_profile']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        Player.objects.create(user=user)
        return user

class MatchmakingSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='player.user.username', read_only=True)

    class Meta:
        model = MatchmakingQueue
        fields = ['id', 'username', 'rating', 'joined_at']

class MoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Move
        fields = '__all__'

class GameSerializer(serializers.ModelSerializer):
    moves = MoveSerializer(many=True, read_only=True)
    player_white_name = serializers.SerializerMethodField()
    player_black_name = serializers.SerializerMethodField()
    winner_name = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = '__all__'

    def get_player_white_name(self, obj):
        return obj.player_white.user.username if obj.player_white else ''

    def get_player_black_name(self, obj):
        return obj.player_black.user.username if obj.player_black else ''

    def get_winner_name(self, obj):
        return obj.winner.user.username if obj.winner else ''

class MoveInputSerializer(serializers.Serializer):
    """
    Validation
    Example JSON:
    {
        "action": "move",
        "from_square": "e2",
        "to_square": "e4",
        "promotion": "Queen"   // not necessary
    }
    """
    from_square = serializers.RegexField(
        regex=r'^[a-h][1-8]$',
        help_text='Square from which the piece is moved, format a1-h8',
    )
    to_square = serializers.RegexField(
        regex=r'^[a-h][1-8]$',
        help_text='Square to which the piece is moved, format a1-h8',
    )
    promotion = serializers.ChoiceField(
        choices=['Queen', 'Rook', 'Bishop', 'Knight'],
        required=False,
        default='Queen',
    )
