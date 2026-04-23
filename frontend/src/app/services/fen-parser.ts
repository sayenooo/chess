export interface Piece {
  type: 'King' | 'Queen' | 'Rook' | 'Bishop' | 'Knight' | 'Pawn';
  color: 'white' | 'black';
}

const PIECE_MAP: Record<string, Piece> = {
  'K': { type: 'King',   color: 'white' },
  'Q': { type: 'Queen',  color: 'white' },
  'R': { type: 'Rook',   color: 'white' },
  'B': { type: 'Bishop', color: 'white' },
  'N': { type: 'Knight', color: 'white' },
  'P': { type: 'Pawn',   color: 'white' },
  'k': { type: 'King',   color: 'black' },
  'q': { type: 'Queen',  color: 'black' },
  'r': { type: 'Rook',   color: 'black' },
  'b': { type: 'Bishop', color: 'black' },
  'n': { type: 'Knight', color: 'black' },
  'p': { type: 'Pawn',   color: 'black' },
};

const UNICODE_PIECES: Record<string, string> = {
  'white_King':   '♔', 'white_Queen':  '♕', 'white_Rook':   '♖',
  'white_Bishop': '♗', 'white_Knight': '♘', 'white_Pawn':   '♙',
  'black_King':   '♚', 'black_Queen':  '♛', 'black_Rook':   '♜',
  'black_Bishop': '♝', 'black_Knight': '♞', 'black_Pawn':   '♟',
};

/**
 * Parse a FEN string into an 8×8 board array.
 * board[0] = rank 8 (top), board[7] = rank 1 (bottom).
 */
export function parseFEN(fen: string): (Piece | null)[][] {
  const board: (Piece | null)[][] = [];
  const ranks = fen.split(' ')[0].split('/');

  for (const rank of ranks) {
    const row: (Piece | null)[] = [];
    for (const ch of rank) {
      if (ch >= '1' && ch <= '8') {
        for (let i = 0; i < parseInt(ch); i++) row.push(null);
      } else {
        row.push(PIECE_MAP[ch] ? { ...PIECE_MAP[ch] } : null);
      }
    }
    board.push(row);
  }

  return board;
}

/** Get the active color from FEN ('white' or 'black'). */
export function fenActiveColor(fen: string): 'white' | 'black' {
  const parts = fen.split(' ');
  return parts[1] === 'b' ? 'black' : 'white';
}

/** Get unicode symbol for a piece. */
export function pieceToUnicode(piece: Piece | null): string {
  if (!piece) return '';
  return UNICODE_PIECES[`${piece.color}_${piece.type}`] ?? '';
}

const TYPE_LETTER: Record<string, string> = {
  'King': 'K', 'Queen': 'Q', 'Rook': 'R', 'Bishop': 'B', 'Knight': 'N', 'Pawn': 'P'
};

/**
 * Get SVG image path for a piece.
 * Files expected at public/pieces/ with names like wK.svg, bQ.svg etc.
 */
export function pieceToImagePath(piece: Piece | null): string {
  if (!piece) return '';
  const c = piece.color === 'white' ? 'w' : 'b';
  return `pieces/${c}${TYPE_LETTER[piece.type]}.svg`;
}
