class Piece:
    def __init__(self, color, position):
        self.color = color
        self.position = position
        self.has_moved = False
        
    def get_possible_moves(self, board):
        raise NotImplementedError("This method should be implemented by subclasses")
    
    def get_legal_moves(self, board):
        pseudo_moves = self.get_possible_moves(board)
        legal_moves = []

        start_row, start_col = self.position

        for move in pseudo_moves:
            end_row, end_col = move
            target_piece = board.grid[end_row][end_col]

            board.grid[end_row][end_col] = self
            board.grid[start_row][start_col] = None
            self.position = (end_row, end_col)

            if not board.is_in_check(self.color):
                legal_moves.append(move)

            self.position = (start_row, start_col)
            board.grid[start_row][start_col] = self
            board.grid[end_row][end_col] = target_piece

        return legal_moves

class Pawn(Piece):
    def get_possible_moves(self, board):
        moves = []
        row, col = self.position
        
        direction = 1 if self.color == 'white' else -1
        start_row = 1 if self.color == 'white' else 6
        
        forward_row = row + direction
        if 0 <= forward_row <= 7 and board.get_piece_at(forward_row, col) is None:
            moves.append((forward_row, col))
            
            double_row = row + 2 * direction
            if row == start_row and board.get_piece_at(double_row, col) is None:
                moves.append((double_row, col))
                
        for dc in [-1, 1]:
            diag_col = col + dc
            if 0 <= forward_row <= 7 and 0 <= diag_col <= 7:
                target_piece = board.get_piece_at(forward_row, diag_col)
                if target_piece is not None and target_piece.color != self.color:
                    moves.append((forward_row, diag_col))
                    
        if board.last_move:
            last_piece, last_start, last_end = board.last_move
            if isinstance(last_piece, Pawn) and last_piece.color != self.color:
                last_start_row, last_start_col = last_start
                last_end_row, last_end_col = last_end
                if abs(last_start_row - last_end_row) == 2 and last_end_row == row:
                    if abs(last_end_col - col) == 1:
                        moves.append((row + direction, last_end_col))
                    
        return moves
    
class Knight(Piece):
    def get_possible_moves(self, board):
        moves = []
        row, col = self.position      
        knight_jumps = [
            (2, 1), (1, 2), (-1, 2), (-2, 1),
            (-2, -1), (-1, -2), (1, -2), (2, -1)
        ]
        for dr, dc in knight_jumps:
            new_row = row + dr
            new_col = col + dc
            if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                target_piece = board.get_piece_at(new_row, new_col)
                if target_piece is None or target_piece.color != self.color:
                    moves.append((new_row, new_col))
                    
        return moves
    
class Bishop(Piece):
    def get_possible_moves(self, board):
        moves = []
        row, col = self.position
        directions = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
        
        for dr, dc in directions:
            current_row, current_col = row, col
            while True:
                current_row += dr
                current_col += dc
                
                if not (0 <= current_row <= 7 and 0 <= current_col <= 7):
                    break
                    
                target_piece = board.get_piece_at(current_row, current_col)
                if target_piece is None:
                    moves.append((current_row, current_col))
                elif target_piece.color != self.color:
                    moves.append((current_row, current_col))
                    break
                else:
                    break
        return moves

class Rook(Piece):
    def get_possible_moves(self, board):
        moves = []
        row, col = self.position
        
        directions = [(1, 0), (-1, 0), (0, -1), (0, 1)]
        
        for dr, dc in directions:
            current_row, current_col = row, col
            
            while True:
                current_row += dr
                current_col += dc
                
                if not (0 <= current_row <= 7 and 0 <= current_col <= 7):
                    break
                    
                target_piece = board.get_piece_at(current_row, current_col)
                
                if target_piece is None:
                    moves.append((current_row, current_col))
                elif target_piece.color != self.color:
                    moves.append((current_row, current_col))
                    break
                else:
                    break
                    
        return moves

class Queen(Piece):
    def get_possible_moves(self, board):
        moves = []
        row, col = self.position
        
        directions = [
            (1, 0), (-1, 0), (0, -1), (0, 1),
            (1, 1), (-1, 1), (-1, -1), (1, -1)
        ]
        
        for dr, dc in directions:
            current_row, current_col = row, col
            while True:
                current_row += dr
                current_col += dc
                if not (0 <= current_row <= 7 and 0 <= current_col <= 7):
                    break
                target_piece = board.get_piece_at(current_row, current_col)
                if target_piece is None:
                    moves.append((current_row, current_col))
                elif target_piece.color != self.color:
                    moves.append((current_row, current_col))
                    break
                else:
                    break
        return moves

class King(Piece):
    def get_possible_moves(self, board):
        moves = []
        row, col = self.position
        directions = [
            (1, 0), (-1, 0), (0, -1), (0, 1),
            (1, 1), (-1, 1), (-1, -1), (1, -1)
        ]
        
        for dr, dc in directions:
            new_row = row + dr
            new_col = col + dc
            
            if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                target_piece = board.get_piece_at(new_row, new_col)
                if target_piece is None or target_piece.color != self.color:
                    moves.append((new_row, new_col))
        
        if not self.has_moved:
            enemy_color = 'black' if self.color == 'white' else 'white'
            if not board.is_under_attack(row, col, enemy_color):
                for rook_col, path in [(0, [1, 2, 3]), (7, [5, 6])]:
                    rook = board.get_piece_at(row, rook_col)
                    if isinstance(rook, Rook) and not rook.has_moved:
                        if all(board.get_piece_at(row, c) is None for c in path):
                            check_path = path[-2:] if rook_col == 0 else path[:2]
                            if all(not board.is_under_attack(row, c, enemy_color) for c in check_path):
                                moves.append((row, 2 if rook_col == 0 else 6))
                    
        return moves