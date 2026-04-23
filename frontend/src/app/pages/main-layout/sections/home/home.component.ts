import { Component, OnInit, inject, input } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import { ApiService, Game, UserProfile } from '../../../../services/api.service';
import { parseFEN, pieceToImagePath, Piece } from '../../../../services/fen-parser';

interface MovePair {
  number: number;
  white: string;
  black: string;
  whiteFen: string;
  blackFen: string;
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, DatePipe],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent implements OnInit {
  readonly user = input<UserProfile | null>(null);
  private api = inject(ApiService);

  games: Game[] = [];
  displayCount = 10;
  loading = true;

  // Replay
  replayOpen = false;
  replayGame: Game | null = null;
  replayMoves: any[] = [];
  replayMovePairs: MovePair[] = [];
  replayIndex = -1; // -1 = start position (before any moves)
  replayBoard: (Piece | null)[][] = [];
  replayLoading = false;

  readonly FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
  readonly RANKS = [8, 7, 6, 5, 4, 3, 2, 1];
  private readonly DEFAULT_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

  async ngOnInit() {
    try {
      this.games = await firstValueFrom(this.api.getGames({ mine: true }));
    } catch {
      // ignore
    } finally {
      this.loading = false;
    }
  }

  get visibleGames(): Game[] {
    return this.games.slice(0, this.displayCount);
  }

  get hasMore(): boolean {
    return this.displayCount < this.games.length;
  }

  showMore() {
    this.displayCount += 10;
  }

  getResult(game: Game): 'win' | 'loss' | 'draw' | 'ongoing' {
    const u = this.user();
    if (game.status === 'IN_PROGRESS' || game.status === 'WAITING') return 'ongoing';
    if (game.status === 'STALEMATE' || game.status === 'DRAW') return 'draw';
    if (!u || game.winner === null) return 'draw';
    if (game.winner === u.id) return 'win';
    return 'loss';
  }

  getResultText(game: Game): string {
    const r = this.getResult(game);
    if (r === 'win') return 'Victory';
    if (r === 'loss') return 'Defeat';
    if (r === 'draw') return 'Draw';
    return 'In Progress';
  }

  getOpponent(game: Game): string {
    const u = this.user();
    if (!u) return '—';
    if (game.game_type === 'SOLO') return 'Solo';
    if (game.game_type === 'BOT') return `Bot (Lv.${game.bot_level || '?'})`;
    if (game.player_white === u.id) return game.player_black_name || '—';
    return game.player_white_name || '—';
  }

  getRatingChange(game: Game): string {
    if (game.game_type !== 'ONLINE') return '';
    const r = this.getResult(game);
    if (r === 'ongoing') return '';
    if (r === 'win') return '+15';
    if (r === 'loss') return '-15';
    return '+0';
  }

  getRatingClass(game: Game): string {
    const r = this.getResult(game);
    if (r === 'win') return 'rating-up';
    if (r === 'loss') return 'rating-down';
    return 'rating-neutral';
  }

  // --- Replay ---

  async openGame(game: Game) {
    this.replayGame = game;
    this.replayLoading = true;
    this.replayOpen = true;

    try {
      const moves = await firstValueFrom(this.api.getGameMoves(game.id));
      this.replayMoves = moves;
      this.buildMovePairs(moves);
      if (moves.length > 0) {
        this.replayIndex = moves.length - 1;
        this.replayBoard = parseFEN(moves[moves.length - 1].fen_after_move || this.DEFAULT_FEN);
      } else {
        this.replayIndex = -1;
        this.replayBoard = parseFEN(game.current_fen || this.DEFAULT_FEN);
      }
    } catch {
      this.replayBoard = parseFEN(game.current_fen || this.DEFAULT_FEN);
      this.replayMoves = [];
      this.buildMovePairs([]);
      this.replayIndex = -1;
    } finally {
      this.replayLoading = false;
    }
  }

  private buildMovePairs(moves: any[]) {
    this.replayMovePairs = [];
    for (let i = 0; i < moves.length; i += 2) {
      const white = moves[i];
      const black = moves[i + 1] || null;
      this.replayMovePairs.push({
        number: Math.floor(i / 2) + 1,
        white: white.notation || `${white.from_square}→${white.to_square}`,
        black: black ? (black.notation || `${black.from_square}→${black.to_square}`) : '',
        whiteFen: white.fen_after_move || this.DEFAULT_FEN,
        blackFen: black ? (black.fen_after_move || this.DEFAULT_FEN) : ''
      });
    }
  }

  goToMove(index: number) {
    if (index < -1 || index >= this.replayMoves.length) return;
    this.replayIndex = index;
    if (index === -1) {
      this.replayBoard = parseFEN(this.DEFAULT_FEN);
    } else {
      this.replayBoard = parseFEN(this.replayMoves[index].fen_after_move || this.DEFAULT_FEN);
    }
  }

  goToStart() { this.goToMove(-1); }
  goToEnd() { this.goToMove(this.replayMoves.length - 1); }
  prevMove() { this.goToMove(this.replayIndex - 1); }
  nextMove() { this.goToMove(this.replayIndex + 1); }

  closeReplay() {
    this.replayOpen = false;
    this.replayGame = null;
    this.replayMoves = [];
    this.replayMovePairs = [];
    this.replayIndex = -1;
  }

  // Board helpers for replay
  getPieceAt(file: string, rank: number): Piece | null {
    const col = this.FILES.indexOf(file);
    const row = 8 - rank;
    return this.replayBoard[row]?.[col] ?? null;
  }

  getPieceImage(piece: Piece | null): string {
    return pieceToImagePath(piece);
  }

  isDark(file: string, rank: number): boolean {
    const col = this.FILES.indexOf(file);
    return (col + rank) % 2 === 0;
  }

  // Check if a move index is currently active
  isMoveActive(pairIndex: number, color: 'white' | 'black'): boolean {
    const moveIdx = pairIndex * 2 + (color === 'black' ? 1 : 0);
    return this.replayIndex === moveIdx;
  }

  onMoveClick(pairIndex: number, color: 'white' | 'black') {
    const moveIdx = pairIndex * 2 + (color === 'black' ? 1 : 0);
    if (moveIdx < this.replayMoves.length) {
      this.goToMove(moveIdx);
    }
  }
}
