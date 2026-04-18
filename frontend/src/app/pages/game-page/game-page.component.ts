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

  board: Piece[] = [];
  currentTurn = '';
  errorMessage = '';

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
          }
        
          if (message.type === 'move_result') {
            this.applyBoardState(message.payload.board);
            this.errorMessage = '';
            this.clearSelection();
                    
            const toSquare = message.payload.to_square;
            if (toSquare) {
              setTimeout(() => {
                const btn = document.querySelector(
                  `[data-square="${toSquare}"]`
                ) as HTMLButtonElement | null;
              
                btn?.click();
              }, 0);
            }
          
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

  getSquares(): string[] {
    const squares: string[] = [];

    for (const rank of this.ranks) {
      for (const file of this.files) {
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
}