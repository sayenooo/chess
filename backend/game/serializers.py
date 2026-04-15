from rest_framework import serializers

from .models import Game, Move

class MoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Move
        fields = '__all__'


class GameSerializer(serializers.ModelSerializer):
    moves = MoveSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = '__all__'

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
