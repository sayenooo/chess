import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { parseFEN, pieceToImagePath, Piece } from '../../../../services/fen-parser';

interface Opening {
  name: string;
  description: string;
  steps: { move: string; fen: string; explanation: string }[];
}

@Component({
  selector: 'app-learn',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './learn.component.html',
  styleUrl: './learn.component.css'
})
export class LearnComponent {
  readonly FILES = ['a','b','c','d','e','f','g','h'];
  readonly RANKS = [8,7,6,5,4,3,2,1];

  selectedOpening: Opening | null = null;
  currentStep = 0;

  readonly openings: Opening[] = [
    {
      name: 'Italian Game',
      description: 'One of the oldest and most classical openings, aiming for rapid development and control of the center.',
      steps: [
        { move: 'Start', fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', explanation: 'Starting position.' },
        { move: '1. e4', fen: 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1', explanation: 'White opens with the King\'s Pawn, immediately fighting for the center.' },
        { move: '1... e5', fen: 'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2', explanation: 'Black mirrors, also contesting the center.' },
        { move: '2. Nf3', fen: 'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2', explanation: 'White develops the knight attacking Black\'s e5 pawn.' },
        { move: '2... Nc6', fen: 'r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3', explanation: 'Black defends e5 while developing a piece.' },
        { move: '3. Bc4', fen: 'r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3', explanation: 'The Italian Game! Bishop targets the f7 square — the weakest point in Black\'s position.' },
      ]
    },
    {
      name: 'Sicilian Defense',
      description: 'The most popular response to 1.e4, leading to sharp, unbalanced positions.',
      steps: [
        { move: 'Start', fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', explanation: 'Starting position.' },
        { move: '1. e4', fen: 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1', explanation: 'White opens with 1.e4.' },
        { move: '1... c5', fen: 'rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2', explanation: 'The Sicilian! Black fights for the d4 square without mirroring White.' },
        { move: '2. Nf3', fen: 'rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2', explanation: 'White develops naturally, preparing d4.' },
        { move: '2... d6', fen: 'rnbqkbnr/pp2pppp/3p4/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3', explanation: 'Black prepares to develop the knight to f6 and keeps a solid structure.' },
      ]
    },
    {
      name: 'Queen\'s Gambit',
      description: 'A classic opening where White offers a pawn to gain central control.',
      steps: [
        { move: 'Start', fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', explanation: 'Starting position.' },
        { move: '1. d4', fen: 'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1', explanation: 'White opens with the Queen\'s Pawn.' },
        { move: '1... d5', fen: 'rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2', explanation: 'Black responds symmetrically.' },
        { move: '2. c4', fen: 'rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2', explanation: 'The Queen\'s Gambit! White offers the c-pawn to disrupt Black\'s center.' },
      ]
    },
    {
      name: 'French Defense',
      description: 'A solid but ambitious defense where Black builds a pawn chain in the center.',
      steps: [
        { move: 'Start', fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', explanation: 'Starting position.' },
        { move: '1. e4', fen: 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1', explanation: 'White opens with 1.e4.' },
        { move: '1... e6', fen: 'rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2', explanation: 'The French! Black prepares to challenge e4 with d5.' },
        { move: '2. d4', fen: 'rnbqkbnr/pppp1ppp/4p3/8/3PP3/8/PPP2PPP/RNBQKBNR b KQkq - 0 2', explanation: 'White establishes a strong pawn center.' },
        { move: '2... d5', fen: 'rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3', explanation: 'Black strikes at the center, creating tension.' },
      ]
    },
    {
      name: 'Ruy López',
      description: 'The Spanish Game — one of the most deeply studied openings, favored by grandmasters.',
      steps: [
        { move: 'Start', fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', explanation: 'Starting position.' },
        { move: '1. e4', fen: 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1', explanation: 'King\'s Pawn opening.' },
        { move: '1... e5', fen: 'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2', explanation: 'Black responds symmetrically.' },
        { move: '2. Nf3', fen: 'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2', explanation: 'Developing and attacking e5.' },
        { move: '2... Nc6', fen: 'r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3', explanation: 'Defending e5.' },
        { move: '3. Bb5', fen: 'r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3', explanation: 'The Ruy López! Bishop pins the knight, putting indirect pressure on e5.' },
      ]
    },
    {
      name: 'King\'s Indian Defense',
      description: 'A hypermodern defense where Black allows White a big center, then strikes back.',
      steps: [
        { move: 'Start', fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', explanation: 'Starting position.' },
        { move: '1. d4', fen: 'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1', explanation: 'Queen\'s Pawn opening.' },
        { move: '1... Nf6', fen: 'rnbqkb1r/pppppppp/5n2/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 1 2', explanation: 'Black develops the knight, delaying pawn moves.' },
        { move: '2. c4', fen: 'rnbqkb1r/pppppppp/5n2/8/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2', explanation: 'White expands in the center.' },
        { move: '2... g6', fen: 'rnbqkb1r/pppppp1p/5np1/8/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3', explanation: 'Black prepares to fianchetto the bishop.' },
        { move: '3. Nc3', fen: 'rnbqkb1r/pppppp1p/5np1/8/2PP4/2N5/PP2PPPP/R1BQKBNR b KQkq - 1 3', explanation: 'White develops, supporting the center.' },
        { move: '3... Bg7', fen: 'rnbqk2r/ppppppbp/5np1/8/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4', explanation: 'The fianchettoed bishop is a powerful piece on the long diagonal.' },
      ]
    },
  ];

  selectOpening(opening: Opening) {
    this.selectedOpening = opening;
    this.currentStep = 0;
  }

  back() {
    this.selectedOpening = null;
    this.currentStep = 0;
  }

  prevStep() {
    if (this.currentStep > 0) this.currentStep--;
  }

  nextStep() {
    if (this.selectedOpening && this.currentStep < this.selectedOpening.steps.length - 1) {
      this.currentStep++;
    }
  }

  get currentFEN(): string {
    return this.selectedOpening?.steps[this.currentStep]?.fen ?? '';
  }

  getBoard(): (Piece | null)[][] {
    return parseFEN(this.currentFEN);
  }

  getPieceImage(piece: Piece | null): string {
    return pieceToImagePath(piece);
  }

  isDark(col: number, row: number): boolean {
    return (col + row) % 2 === 1;
  }
}
