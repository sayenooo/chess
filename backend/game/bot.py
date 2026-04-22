from stockfish import Stockfish
from django.conf import settings
import os

class ChessBot:
    def __init__(self, level: int):
        engine_path = os.path.join(settings.BASE_DIR, 'game', 'engine', 'stockfish-windows-x86-64-avx2.exe')
        
        self.stockfish = Stockfish(path=engine_path)
        
        self._set_difficulty(level)

    def _set_difficulty(self, level: int):
        if level == 1:
            self.stockfish.set_skill_level(0)
            self.stockfish.set_depth(1)
        elif level == 2:
            self.stockfish.set_skill_level(5)
            self.stockfish.set_depth(3)
        elif level == 3:
            self.stockfish.set_skill_level(10)
            self.stockfish.set_depth(5)
        elif level == 4:
            self.stockfish.set_skill_level(15)
            self.stockfish.set_depth(8)
        else:
            self.stockfish.set_skill_level(20)
            self.stockfish.set_depth(12)

    def get_best_move(self, fen: str) -> dict:
        self.stockfish.set_fen_position(fen)
        best_move_str = self.stockfish.get_best_move()
        
        if not best_move_str:
            return None
            
        move_data = {
            'action': 'move',
            'from_square': best_move_str[0:2],
            'to_square': best_move_str[2:4]
        }
        
        if len(best_move_str) == 5:
            prom_char = best_move_str[4].upper()
            promotion_map = {'Q': 'Queen', 'R': 'Rook', 'B': 'Bishop', 'N': 'Knight'}
            move_data['promotion'] = promotion_map.get(prom_char, 'Queen')

        return move_data