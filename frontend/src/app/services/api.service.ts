import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Game {
  id: number;
  game_type: 'SOLO' | 'ONLINE' | 'BOT';
  player_white: string;
  player_black: string;
  current_fen: string;
  status: string;
  winner: string | null;
  created_at: string;
  last_move_at: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = 'http://127.0.0.1:8000/api';

  getGames(): Observable<Game[]> {
    return this.http.get<Game[]>(`${this.baseUrl}/games/`);
  }

  getGameById(id: number): Observable<Game> {
    return this.http.get<Game>(`${this.baseUrl}/games/${id}/`);
  }

  createGame(gameType: 'SOLO' | 'ONLINE' | 'BOT') {
    return this.http.post<Game>(`${this.baseUrl}/games/`, {
      game_type: gameType
    });
  }

  getMoves(gameId: number) {
    return this.http.get(`${this.baseUrl}/games/${gameId}/moves/`);
  }
}