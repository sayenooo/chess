from rest_framework import serializers

from .models import Game, Move


# ───────────────────────────────────────────────
# REST API сериализаторы (для будущего REST API)
# ───────────────────────────────────────────────

class MoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Move
        fields = '__all__'


class GameSerializer(serializers.ModelSerializer):
    moves = MoveSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = '__all__'


# ───────────────────────────────────────────────
# WebSocket входные сериализаторы
# ───────────────────────────────────────────────
# Это НЕ ModelSerializer: они только валидируют JSON
# от фронтенда, не привязаны к БД.
# ───────────────────────────────────────────────

class MoveInputSerializer(serializers.Serializer):
    """
    Валидация хода, полученного через WebSocket.

    Пример JSON от фронта:
    {
        "action": "move",
        "from_square": "e2",
        "to_square": "e4",
        "promotion": "Queen"   // необязательно
    }
    """
    from_square = serializers.RegexField(
        regex=r'^[a-h][1-8]$',
        help_text='Клетка откуда ходим, формат a1-h8',
    )
    to_square = serializers.RegexField(
        regex=r'^[a-h][1-8]$',
        help_text='Клетка куда ходим, формат a1-h8',
    )
    promotion = serializers.ChoiceField(
        choices=['Queen', 'Rook', 'Bishop', 'Knight'],
        required=False,
        default='Queen',
    )
