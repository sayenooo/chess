import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-not-found',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="not-found">
      <div class="nf-card">
        <span class="nf-icon">♚</span>
        <h1>404</h1>
        <p>This page doesn't exist — just like a legal move after checkmate.</p>
        <a href="/" class="nf-btn">Return Home</a>
      </div>
    </div>
  `,
  styles: [`
    .not-found {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #0d0d0d 0%, #1a1a1a 50%, #121212 100%);
    }
    .nf-card {
      text-align: center;
      padding: 60px 48px;
      animation: fadeUp 0.5s ease;
    }
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .nf-icon {
      font-size: 72px;
      display: block;
      margin-bottom: 16px;
      opacity: 0.4;
    }
    h1 {
      font-size: 80px;
      font-weight: 800;
      color: #c9a84c;
      margin-bottom: 12px;
      letter-spacing: -2px;
    }
    p {
      color: #777;
      font-size: 16px;
      margin-bottom: 28px;
    }
    .nf-btn {
      display: inline-block;
      padding: 14px 32px;
      background: linear-gradient(135deg, #c9a84c, #a88a3a);
      color: #111;
      font-weight: 600;
      font-size: 15px;
      border-radius: 10px;
      text-decoration: none;
      transition: all 0.25s ease;
    }
    .nf-btn:hover {
      background: linear-gradient(135deg, #dbb85c, #b89a4a);
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(201, 168, 76, 0.3);
    }
  `]
})
export class NotFoundComponent {}
