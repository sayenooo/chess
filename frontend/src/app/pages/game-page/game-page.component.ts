import {
  Component,
  OnDestroy,
  OnInit,
  inject,
  NgZone,
  ChangeDetectorRef
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { GameService } from '../../services/game.service';

interface Piece {
  square: string;
  type: 'Pawn' | 'Rook' | 'Knight' | 'Bishop' | 'Queen' | 'King';
  color: 'white' | 'black';
}

@Component({
  selector: 'app-game-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './game-page.component.html',
  styleUrl: './game-page.component.css'
})
export class GamePageComponent implements OnInit, OnDestroy {
  private gameService = inject(GameService);
  private ngZone = inject(NgZone);
  private cdr = inject(ChangeDetectorRef);
  private sub?: Subscription;
  private clickBoardAfterNewGame = false;

  board: Piece[] = [];
  currentTurn = '';
  errorMessage = '';
  boardFlipped = false;

  selectedFrom: string | null = null;
  selectedTo: string | null = null;

  readonly files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
  readonly ranks = [8, 7, 6, 5, 4, 3, 2, 1];

  ngOnInit(): void {
    this.sub = this.gameService.connect('solo1', 'solo').subscribe({
      next: (message) => {
        this.ngZone.run(() => {
          if (message.type === 'game_state') {
            this.applyBoardState(message.payload);
            this.errorMessage = '';
            this.clearSelection();

            if (this.clickBoardAfterNewGame) {
              this.clickBoardAfterNewGame = false;
              this.boardFlipped = false;
              this.cdr.detectChanges();
              this.clickSquareAfterRender('a8');
            } else {
              this.cdr.detectChanges();
            }

            return;
          }
        
          if (message.type === 'move_result') {
            this.applyBoardState(message.payload.board);
            this.errorMessage = '';
            this.clearSelection();
            this.switchBoardSideAfterMove();
            this.cdr.detectChanges();
                    
            const toSquare = message.payload.to_square;
            this.clickSquareAfterRender(toSquare);
          
            return;
          }
        
          if (message.type === 'error') {
            this.errorMessage = message.payload.message ?? 'Invalid move';
            this.clearSelection();
            this.cdr.detectChanges();
          }
        });
      },
      error: (err) => {
        console.error('WebSocket error:', err);
      }
    });
  }

  private applyBoardState(state: any): void {
    this.board = [...(state?.board ?? [])];
    this.currentTurn = state?.current_turn ?? this.currentTurn;
  }

  private clickSquareAfterRender(square: string | null | undefined): void {
    if (!square) return;

    setTimeout(() => {
      const btn = document.querySelector(
        `[data-square="${square}"]`
      ) as HTMLButtonElement | null;

      btn?.click();
    }, 0);
  }

  getSquares(): string[] {
    const squares: string[] = [];
    const files = this.boardFlipped ? [...this.files].reverse() : this.files;
    const ranks = this.boardFlipped ? [...this.ranks].reverse() : this.ranks;

    for (const rank of ranks) {
      for (const file of files) {
        squares.push(`${file}${rank}`);
      }
    }

    return squares;
  }

  getPieceAt(square: string): Piece | undefined {
    return this.board.find(piece => piece.square === square);
  }

  getPieceSymbol(square: string): string {
    const piece = this.getPieceAt(square);
    if (!piece) return '';

    const symbols: Record<string, string> = {
      white_King: '♔',
      white_Queen: '♕',
      white_Rook: '♖',
      white_Bishop: '♗',
      white_Knight: '♘',
      white_Pawn: '♙',
      black_King: '♚',
      black_Queen: '♛',
      black_Rook: '♜',
      black_Bishop: '♝',
      black_Knight: '♞',
      black_Pawn: '♟'
    };

    return symbols[`${piece.color}_${piece.type}`] ?? '';
  }

  isDarkSquare(square: string): boolean {
    const file = square.charCodeAt(0) - 97;
    const rank = Number(square[1]);
    return (file + rank) % 2 === 1;
  }

  onSquareClick(square: string): void {
    console.log('clicked:', square);
    this.errorMessage = '';

    const clickedPiece = this.getPieceAt(square);

    if (!this.selectedFrom) {
      if (!this.isPieceSelectable(clickedPiece)) {
        return;
      }
      this.selectedFrom = square;
      return;
    }

    if (this.selectedFrom === square) {
      this.clearSelection();
      return;
    }

    if (this.isPieceSelectable(clickedPiece)) {
      this.selectedFrom = square;
      this.selectedTo = null;
      return;
    }

    this.selectedTo = square;
    console.log('sending move:', this.selectedFrom, this.selectedTo);
    this.gameService.sendMove(this.selectedFrom, this.selectedTo);
  }

  isSelected(square: string): boolean {
    return this.selectedFrom === square || this.selectedTo === square;
  }

  clearSelection(): void {
    this.selectedFrom = null;
    this.selectedTo = null;
  }

  trackBySquare(_: number, square: string): string {
    return square;
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
    this.gameService.disconnect();
  }

  private isPieceSelectable(piece: Piece | undefined): boolean {
    if (!piece) return false;
    return piece.color === this.currentTurn;
  }

  // chess right side settings
  gameMode: 'bot' | 'pvp' = 'bot';
  botDifficulty: 'easy' | 'medium' | 'hard' = 'medium';
  playerSide: 'white' | 'black' = 'white';
  switchSidesAfterMove = true;

  moves: string[] = [];

  selectGameMode(mode: 'bot' | 'pvp'): void {
    this.gameMode = mode;
  }

  selectDifficulty(level: 'easy' | 'medium' | 'hard'): void {
    this.botDifficulty = level;
  }

  selectSide(side: 'white' | 'black'): void {
    this.playerSide = side;
  }

  setSwitchSides(value: boolean): void {
    this.switchSidesAfterMove = value;
  }

  switchBoardSideAfterMove(): void {
    if (!this.switchSidesAfterMove) return;

    this.boardFlipped = !this.boardFlipped;
  }

  startGame(): void {
    console.log('Start game');
  }

  // move history
  // moves: string[] = [];
  // if (message.type === 'move_result') {
  //   const move = message.payload;
    
  //   const moveText = `${move.from_square} ${move.to_square}`;
    
  //   this.moves.push(moveText);
  // }
  // const moveText = `${move.from_square.toUpperCase()} → ${move.to_square.toUpperCase()}`;
  // let moveText = `${move.from_square.toUpperCase()} → ${move.to_square.toUpperCase()}`;

  // if (move.captured) {
  //   moveText += ' (x)';
  //}

  newGame(): void {
    this.clickBoardAfterNewGame = true;
    this.gameService.newGame();
  }
  
  resign(): void {
    this.gameService.resign();
  }
}
