from .pieces import Pawn, Rook, Knight, Bishop, Queen, King

CHARS = 'abcdefgh'

def parse_square(square: str) -> tuple[int, int]:
    """'e2' → (1, 4)."""
    col = CHARS.index(square[0])
    row = int(square[1]) - 1
    return row, col


def format_square(row: int, col: int) -> str:
    """(1, 4) → 'e2'."""
    return f'{CHARS[col]}{row + 1}'


class Board:
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.current_turn = 'white'
        self.last_move = None
        self.move_count = 0
        self.setup_starting_position()

    def setup_starting_position(self):
        for col in range(8):
            self.place_piece(Pawn('white', (1, col)), 1, col)
            self.place_piece(Pawn('black', (6, col)), 6, col)

        piece_classes = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]

        for col, piece_class in enumerate(piece_classes):
            self.place_piece(piece_class('white', (0, col)), 0, col)
            self.place_piece(piece_class('black', (7, col)), 7, col)

    def get_piece_at(self, row, col):
        if 0 <= row <= 7 and 0 <= col <= 7:
            return self.grid[row][col]
        return None

    def place_piece(self, piece, row, col):
        self.grid[row][col] = piece
        piece.position = (row, col)

    def is_under_attack(self, row, col, enemy_color):
        for r in range(8):
            for c in range(8):
                piece = self.get_piece_at(r, c)
                if piece and piece.color == enemy_color:
                    if piece.__class__.__name__ == 'King':
                        if abs(r - row) <= 1 and abs(c - col) <= 1:
                            return True
                    elif piece.__class__.__name__ == 'Pawn':
                        direction = 1 if piece.color == 'white' else -1
                        if row == r + direction and abs(col - c) == 1:
                            return True
                    else:
                        moves = piece.get_possible_moves(self)
                        if (row, col) in moves:
                            return True

        return False

    def is_in_check(self, color):
        enemy_color = 'black' if color == 'white' else 'white'
        king_pos = None

        for r in range(8):
            for c in range(8):
                piece = self.get_piece_at(r, c)
                if piece and piece.color == color and piece.__class__.__name__ == 'King':
                    king_pos = (r, c)
                    break
            if king_pos:
                break

        if king_pos:
            return self.is_under_attack(king_pos[0], king_pos[1], enemy_color)
        return False

    def has_any_valid_moves(self, color):
        for r in range(8):
            for c in range(8):
                piece = self.get_piece_at(r, c)
                if piece and piece.color == color:
                    if len(piece.get_legal_moves(self)) > 0:
                        return True
        return False

    def is_checkmate(self, color):
        return self.is_in_check(color) and not self.has_any_valid_moves(color)

    def is_stalemate(self, color):
        return not self.is_in_check(color) and not self.has_any_valid_moves(color)

    def move_piece(self, start_pos, end_pos, promotion_choice='Queen'):
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        piece = self.grid[start_row][start_col]

        if piece is None:
            return

        # --- En passant ---
        captured_piece = self.grid[end_row][end_col]
        if isinstance(piece, Pawn) and start_col != end_col:
            if self.grid[end_row][end_col] is None:
                captured_piece = self.grid[start_row][end_col]
                self.grid[start_row][end_col] = None

        # --- Castling ---
        if isinstance(piece, King) and abs(start_col - end_col) == 2:
            if end_col == 6:
                rook = self.grid[start_row][7]
                self.grid[start_row][7] = None
                self.grid[start_row][5] = rook
                rook.position = (start_row, 5)
                rook.has_moved = True
            elif end_col == 2:
                rook = self.grid[start_row][0]
                self.grid[start_row][0] = None
                self.grid[start_row][3] = rook
                rook.position = (start_row, 3)
                rook.has_moved = True

        # --- Pawn promotion ---
        if isinstance(piece, Pawn):
            if (piece.color == 'white' and end_row == 7) or (piece.color == 'black' and end_row == 0):
                choices = {
                    'Queen': Queen,
                    'Rook': Rook,
                    'Bishop': Bishop,
                    'Knight': Knight,
                }
                new_piece_class = choices.get(promotion_choice, Queen)
                piece = new_piece_class(piece.color, (end_row, end_col))

        self.grid[start_row][start_col] = None
        self.grid[end_row][end_col] = piece

        piece.position = (end_row, end_col)
        piece.has_moved = True
        self.last_move = (piece, start_pos, end_pos)
        self.move_count += 1
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'

        return captured_piece
    
    def get_fen(self) -> str:
        fen_rows = []
        for row in range(7, -1, -1):
            empty_count = 0
            row_fen = ""
            for col in range(8):
                piece = self.grid[row][col]
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row_fen += str(empty_count)
                        empty_count = 0
                    
                    p_name = piece.__class__.__name__
                    if p_name == 'Knight': char = 'N'
                    elif p_name == 'Bishop': char = 'B'
                    elif p_name == 'Rook': char = 'R'
                    elif p_name == 'Queen': char = 'Q'
                    elif p_name == 'King': char = 'K'
                    else: char = 'P'
                    
                    if piece.color == 'black':
                        char = char.lower()
                        
                    row_fen += char
            
            if empty_count > 0:
                row_fen += str(empty_count)
            fen_rows.append(row_fen)
            
        piece_placement = "/".join(fen_rows)
        active_color = 'w' if self.current_turn == 'white' else 'b'
        
        castling = ""
        wk = self.grid[0][4]
        if wk and wk.__class__.__name__ == 'King' and wk.color == 'white' and not wk.has_moved:
            rr = self.grid[0][7]
            if rr and rr.__class__.__name__ == 'Rook' and rr.color == 'white' and not rr.has_moved:
                castling += 'K'
            lr = self.grid[0][0]
            if lr and lr.__class__.__name__ == 'Rook' and lr.color == 'white' and not lr.has_moved:
                castling += 'Q'
        bk = self.grid[7][4]
        if bk and bk.__class__.__name__ == 'King' and bk.color == 'black' and not bk.has_moved:
            rr = self.grid[7][7]
            if rr and rr.__class__.__name__ == 'Rook' and rr.color == 'black' and not rr.has_moved:
                castling += 'k'
            lr = self.grid[7][0]
            if lr and lr.__class__.__name__ == 'Rook' and lr.color == 'black' and not lr.has_moved:
                castling += 'q'
                
        if not castling:
            castling = "-"
            
        en_passant = "-"
        halfmove = "0"
        fullmove = str((self.move_count // 2) + 1)
        
        return f"{piece_placement} {active_color} {castling} {en_passant} {halfmove} {fullmove}"
    
    def get_all_legal_moves(self) -> dict:
        """Returns dict { 'e2': ['e3', 'e4'], 'g1': ['f3', 'h3'] ... }"""
        all_moves = {}
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and piece.color == self.current_turn:
                    pos = format_square(row, col)
                    moves = piece.get_legal_moves(self)
                    if moves:
                        all_moves[pos] = [format_square(r, c) for r, c in moves]
        return all_moves