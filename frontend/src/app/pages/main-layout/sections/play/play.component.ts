import { Component, Input, Output, EventEmitter, OnDestroy, OnInit, inject, NgZone, ChangeDetectorRef, afterNextRender } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { ApiService, Game, UserProfile } from '../../../../services/api.service';
import { GameService } from '../../../../services/game.service';
import { parseFEN, pieceToImagePath, Piece } from '../../../../services/fen-parser';

type PlayState = 'idle' | 'matchmaking' | 'opponent_found' | 'playing' | 'game_over';

interface GameOverData {
  reason: string;
  winner: string;
  resignedBy?: string;
}

interface MovePair {
  number: number;
  white: string;
  black: string;
}

@Component({
  selector: 'app-play',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './play.component.html',
  styleUrl: './play.component.css'
})
export class PlayComponent implements OnInit, OnDestroy {
  @Input() user: UserProfile | null = null;
  @Output() gameLock = new EventEmitter<boolean>();
  private api = inject(ApiService);
  private gameService = inject(GameService);
  private ngZone = inject(NgZone);
  private cdr = inject(ChangeDetectorRef);

  // State
  state: PlayState = 'idle';

  // Mode selection
  gameMode: 'SOLO' | 'BOT' | 'ONLINE' = 'SOLO';
  botLevel = 3;
  selectedSide: 'white' | 'black' | 'random' = 'random';
  timeControl = 15; // minutes
  readonly timeOptions = [5, 10, 15, 30];

  // Game state
  gameId: number | null = null;
  playerColor: 'white' | 'black' | 'both' = 'both';
  currentTurn = 'white';
  boardData: (Piece | null)[][] = [];
  selectedSquare: string | null = null;
  errorMessage = '';
  gameStatus = '';
  moveHistory: MovePair[] = [];

  // Timer
  whiteTime = 900;
  blackTime = 900;
  private timerInterval?: ReturnType<typeof setInterval>;

  // Draw offer
  drawOfferReceived = false;
  drawOfferSent = false;
  drawOfferBy = '';

  // Players
  opponentName = 'Opponent';
  opponentRating = 500;

  // Game Over
  gameOverData: GameOverData | null = null;
  ratingChange = 0;

  // Rejoin
  activeGame: Game | null = null;

  // Board
  readonly FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
  readonly RANKS = [8, 7, 6, 5, 4, 3, 2, 1];
  private readonly DEFAULT_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

  // Subscriptions
  private wsSub?: Subscription;
  private matchmakingTimeout?: ReturnType<typeof setTimeout>;
  private totalMoves = 0;

  constructor() {
    this.boardData = parseFEN(this.DEFAULT_FEN);
    afterNextRender(() => {
      this.checkActiveGames();
    });
  }

  ngOnInit() {}

  // --- Board helpers ---

  get isFlipped(): boolean {
    return this.playerColor === 'black';
  }

  get displayFiles(): string[] {
    return this.isFlipped ? [...this.FILES].reverse() : this.FILES;
  }

  get displayRanks(): number[] {
    return this.isFlipped ? [...this.RANKS].reverse() : this.RANKS;
  }

  getPieceAt(file: string, rank: number): Piece | null {
    const col = this.FILES.indexOf(file);
    const row = 8 - rank;
    return this.boardData[row]?.[col] ?? null;
  }

  getPieceImage(piece: Piece | null): string {
    return pieceToImagePath(piece);
  }

  isDark(file: string, rank: number): boolean {
    const col = this.FILES.indexOf(file);
    return (col + rank) % 2 === 0;
  }

  isSelected(file: string, rank: number): boolean {
    return this.selectedSquare === `${file}${rank}`;
  }

  get playerName(): string {
    return this.user?.username ?? 'Player';
  }

  get playerRating(): number {
    return this.user?.player_profile?.rating ?? 500;
  }

  // --- Timer ---

  formatTime(seconds: number): string {
    const m = Math.floor(Math.max(0, seconds) / 60);
    const s = Math.floor(Math.max(0, seconds) % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  }

  get whiteTimeFormatted(): string { return this.formatTime(this.whiteTime); }
  get blackTimeFormatted(): string { return this.formatTime(this.blackTime); }

  get isWhiteLowTime(): boolean { return this.whiteTime < 60; }
  get isBlackLowTime(): boolean { return this.blackTime < 60; }

  private startTimer() {
    this.stopTimer();
    this.timerInterval = setInterval(() => {
      if (this.state !== 'playing') return;
      if (this.currentTurn === 'white') {
        this.whiteTime = Math.max(0, this.whiteTime - 0.1);
        if (this.whiteTime <= 0) {
          this.stopTimer();
        }
      } else {
        this.blackTime = Math.max(0, this.blackTime - 0.1);
        if (this.blackTime <= 0) {
          this.stopTimer();
        }
      }
      this.cdr.detectChanges();
    }, 100);
  }

  private stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = undefined;
    }
  }

  // --- Check for active games (rejoin) ---

  private checkActiveGames() {
    this.api.getActiveGames().subscribe({
      next: (games) => {
        this.ngZone.run(() => {
          const onlineGame = games.find(g => g.game_type === 'ONLINE');
          const botGame = games.find(g => g.game_type === 'BOT');
          this.activeGame = onlineGame || botGame || null;
          this.cdr.detectChanges();
        });
      }
    });
  }

  resumeGame(game: Game) {
    this.gameId = game.id;
    this.gameMode = game.game_type as 'SOLO' | 'BOT' | 'ONLINE';
    this.loadOpponentInfo(game);
    this.connectWebSocket();
  }

  // --- Square click ---

  onSquareClick(file: string, rank: number) {
    if (this.state !== 'playing') return;
    const square = `${file}${rank}`;
    const piece = this.getPieceAt(file, rank);

    if (!this.selectedSquare) {
      if (piece && this.canSelect(piece)) {
        this.selectedSquare = square;
      }
      return;
    }

    if (this.selectedSquare === square) {
      this.selectedSquare = null;
      return;
    }

    if (piece && this.canSelect(piece)) {
      this.selectedSquare = square;
      return;
    }

    this.gameService.sendMove(this.selectedSquare, square);
    this.selectedSquare = null;
  }

  private canSelect(piece: Piece): boolean {
    if (this.playerColor === 'both') return piece.color === this.currentTurn;
    return piece.color === this.playerColor && piece.color === this.currentTurn;
  }

  // --- Start game ---

  startGame() {
    this.errorMessage = '';
    if (this.gameMode === 'ONLINE') {
      this.startMatchmaking();
    } else {
      this.createAndConnect();
    }
  }

  private createAndConnect() {
    const data: any = {
      game_type: this.gameMode,
      side: this.selectedSide,
      time_control: this.gameMode === 'BOT' ? this.timeControl : 15
    };
    if (this.gameMode === 'BOT') data.bot_level = this.botLevel;

    this.api.createGame(data).subscribe({
      next: (game) => {
        this.gameId = game.id;
        this.loadOpponentInfo(game);
        this.connectWebSocket();
      },
      error: () => (this.errorMessage = 'Failed to create game')
    });
  }

  // --- Matchmaking ---

  private startMatchmaking() {
    this.state = 'matchmaking';
    this.gameLock.emit(true);
    this.pollMatchmaking();
  }

  private pollMatchmaking() {
    this.api.joinMatchmaking().subscribe({
      next: (res) => {
        if (res.status === 'game_found' && res.game_id) {
          this.gameId = res.game_id;
          this.state = 'opponent_found';
          this.api.getGameById(res.game_id).subscribe({
            next: (game) => {
              this.loadOpponentInfo(game);
              this.cdr.detectChanges();
            }
          });
          setTimeout(() => {
            this.ngZone.run(() => {
              this.connectWebSocket();
              this.cdr.detectChanges();
            });
          }, 2000);
        } else {
          this.matchmakingTimeout = setTimeout(() => this.pollMatchmaking(), 2000);
        }
      },
      error: () => {
        this.matchmakingTimeout = setTimeout(() => this.pollMatchmaking(), 2000);
      }
    });
  }

  cancelMatchmaking() {
    if (this.matchmakingTimeout) clearTimeout(this.matchmakingTimeout);
    this.api.leaveMatchmaking().subscribe();
    this.state = 'idle';
    this.gameLock.emit(false);
  }

  private loadOpponentInfo(game: Game) {
    if (!this.user) return;
    if (game.player_white_name === this.user.username) {
      this.opponentName = game.player_black_name || 'Bot';
    } else {
      this.opponentName = game.player_white_name || 'Bot';
    }
    this.opponentRating = 500;
  }

  // --- WebSocket ---

  private connectWebSocket() {
    this.state = 'playing';
    this.moveHistory = [];
    this.totalMoves = 0;
    this.errorMessage = '';
    this.selectedSquare = null;
    this.drawOfferReceived = false;
    this.drawOfferSent = false;
    this.activeGame = null;

    if (this.gameMode === 'ONLINE') {
      this.gameLock.emit(true);
    }

    this.wsSub = this.gameService.connect(String(this.gameId)).subscribe({
      next: (msg) => {
        this.ngZone.run(() => {
          this.handleMessage(msg);
          this.cdr.detectChanges();
        });
      },
      error: (err) => {
        console.error('WebSocket error:', err);
        this.errorMessage = 'Connection lost';
      }
    });
  }

  private handleMessage(msg: any) {
    switch (msg.type) {
      case 'connection_established':
        this.playerColor = msg.color;
        this.whiteTime = msg.white_time ?? 900;
        this.blackTime = msg.black_time ?? 900;
        this.currentTurn = msg.current_turn ?? 'white';
        this.gameService.getState();
        this.startTimer();
        break;

      case 'game_state':
        this.boardData = parseFEN(msg.payload.fen);
        this.currentTurn = msg.payload.current_turn;
        this.gameStatus = msg.payload.status;
        if (msg.payload.white_time !== undefined) {
          this.whiteTime = msg.payload.white_time;
          this.blackTime = msg.payload.black_time;
        }
        break;

      case 'move_result':
        this.boardData = parseFEN(msg.payload.fen);
        this.currentTurn = msg.payload.current_turn;
        this.selectedSquare = null;
        this.errorMessage = '';
        this.drawOfferReceived = false;
        this.drawOfferSent = false;

        // Sync timer from server
        if (msg.payload.white_time !== undefined) {
          this.whiteTime = msg.payload.white_time;
          this.blackTime = msg.payload.black_time;
        }

        // Notation
        const notation = msg.payload.notation || `${msg.payload.from_square}→${msg.payload.to_square}`;
        this.totalMoves++;
        if (this.totalMoves % 2 === 1) {
          this.moveHistory.push({
            number: Math.ceil(this.totalMoves / 2),
            white: notation,
            black: ''
          });
        } else {
          if (this.moveHistory.length > 0) {
            this.moveHistory[this.moveHistory.length - 1].black = notation;
          }
        }
        break;

      case 'game_over':
        this.handleGameOver(msg.payload);
        break;

      case 'draw_offer':
        if (msg.payload.offered_by !== this.playerColor) {
          this.drawOfferReceived = true;
          this.drawOfferBy = msg.payload.offered_by;
        } else {
          this.drawOfferSent = true;
        }
        break;

      case 'draw_declined':
        this.drawOfferSent = false;
        this.drawOfferReceived = false;
        break;

      case 'error':
        this.errorMessage = msg.payload.message || 'Error';
        this.selectedSquare = null;
        break;
    }
  }

  private handleGameOver(payload: any) {
    this.stopTimer();
    this.gameOverData = {
      reason: payload.reason,
      winner: payload.winner || '',
      resignedBy: payload.resigned_by
    };
    this.state = 'game_over';

    if (this.gameMode === 'ONLINE') {
      if (this.isPlayerWinner) this.ratingChange = 15;
      else if (this.isPlayerLoser) this.ratingChange = -15;
      else this.ratingChange = 0;
    } else {
      this.ratingChange = 0;
    }
  }

  // --- Game Over helpers ---

  get isPlayerWinner(): boolean {
    if (!this.gameOverData?.winner) return false;
    if (this.playerColor === 'both') return false;
    return this.gameOverData.winner === this.playerColor;
  }

  get isPlayerLoser(): boolean {
    if (!this.gameOverData?.winner) return false;
    if (this.playerColor === 'both') return false;
    return this.gameOverData.winner !== this.playerColor;
  }

  get isDraw(): boolean {
    return this.gameOverData?.reason === 'stalemate' || this.gameOverData?.reason === 'draw' || !this.gameOverData?.winner;
  }

  get resultText(): string {
    if (!this.gameOverData) return '';
    switch (this.gameOverData.reason) {
      case 'checkmate': return 'Checkmate';
      case 'stalemate': return 'Draw';
      case 'draw': return 'Draw';
      case 'timeout': return 'Time Out';
      case 'resign': return this.gameOverData.resignedBy === this.playerColor ? 'You resigned' : 'Opponent resigned';
      default: return 'Game Over';
    }
  }

  get resultSubtext(): string {
    if (this.gameOverData?.reason === 'stalemate') return 'Stalemate — neither side can win';
    if (this.gameOverData?.reason === 'draw') return 'Both players agreed to a draw';
    if (this.gameOverData?.reason === 'timeout') return this.isPlayerWinner ? 'Opponent ran out of time!' : 'You ran out of time';
    if (this.gameOverData?.reason === 'checkmate') return this.isPlayerWinner ? 'You delivered checkmate!' : 'You got checkmated';
    return '';
  }

  get playerResultClass(): string {
    if (this.isDraw) return 'draw-bg';
    return this.isPlayerWinner ? 'winner-bg' : 'loser-bg';
  }

  get opponentResultClass(): string {
    if (this.isDraw) return 'draw-bg';
    return this.isPlayerWinner ? 'loser-bg' : 'winner-bg';
  }

  get resultTextClass(): string {
    if (this.isDraw) return 'text-draw';
    return this.isPlayerWinner ? 'text-win' : 'text-loss';
  }

  get ratingChangeClass(): string {
    if (this.ratingChange > 0) return 'text-win';
    if (this.ratingChange < 0) return 'text-loss';
    return 'text-draw';
  }

  get ratingChangeText(): string {
    if (this.ratingChange > 0) return `+${this.ratingChange}`;
    if (this.ratingChange < 0) return `${this.ratingChange}`;
    return '+0';
  }

  get showRatingChange(): boolean {
    return this.gameMode === 'ONLINE';
  }

  // --- Draw actions ---

  offerDraw() { this.gameService.offerDraw(); }
  acceptDraw() { this.gameService.respondDraw(true); this.drawOfferReceived = false; }
  declineDraw() { this.gameService.respondDraw(false); this.drawOfferReceived = false; }

  // --- Actions ---

  resign() { this.gameService.resign(); }

  exitGame() {
    this.cleanup();
    this.state = 'idle';
    this.boardData = parseFEN(this.DEFAULT_FEN);
    this.gameOverData = null;
    this.moveHistory = [];
    this.totalMoves = 0;
    this.playerColor = 'both';
    this.selectedSquare = null;
    this.errorMessage = '';
    this.drawOfferReceived = false;
    this.drawOfferSent = false;
    this.gameLock.emit(false);
    this.checkActiveGames();
  }

  newGameFromOverlay() {
    this.cleanup();
    this.gameOverData = null;
    this.moveHistory = [];
    this.totalMoves = 0;
    this.startGame();
  }

  private cleanup() {
    this.stopTimer();
    this.wsSub?.unsubscribe();
    this.gameService.disconnect();
    if (this.matchmakingTimeout) clearTimeout(this.matchmakingTimeout);
  }

  ngOnDestroy() {
    this.cleanup();
    this.gameLock.emit(false);
  }
}
