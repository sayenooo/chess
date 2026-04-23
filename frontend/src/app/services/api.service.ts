import { Injectable, inject, PLATFORM_ID } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { isPlatformBrowser } from '@angular/common';

export interface PlayerProfile {
  rating: number;
  bio: string;
  created_at: string;
  wins: number;
  losses: number;
  draws: number;
  avatar: string | null;
}

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  player_profile: PlayerProfile;
}

export interface Game {
  id: number;
  game_type: 'SOLO' | 'ONLINE' | 'BOT';
  player_white: number | null;
  player_black: number | null;
  player_white_name: string;
  player_black_name: string;
  winner: number | null;
  winner_name: string;
  current_fen: string;
  status: string;
  bot_level: number | null;
  created_at: string;
  last_move_at: string | null;
  moves: any[];
}

export interface MatchmakingResponse {
  status: 'searching' | 'game_found';
  game_id?: number;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private platformId = inject(PLATFORM_ID);
  private baseUrl = 'http://127.0.0.1:8000/api';

  private get isBrowser(): boolean {
    return isPlatformBrowser(this.platformId);
  }

  // --- Auth ---

  register(username: string, email: string, password: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/register/`, { username, email, password });
  }

  login(username: string, password: string): Observable<{ access: string; refresh: string }> {
    return this.http
      .post<{ access: string; refresh: string }>(`${this.baseUrl}/login/`, { username, password })
      .pipe(
        tap((res) => {
          if (this.isBrowser) {
            localStorage.setItem('access_token', res.access);
            localStorage.setItem('refresh_token', res.refresh);
          }
        })
      );
  }

  logout(): void {
    if (this.isBrowser) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  getToken(): string | null {
    return this.isBrowser ? localStorage.getItem('access_token') : null;
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  refreshToken(): Observable<{ access: string }> {
    const refresh = this.isBrowser ? localStorage.getItem('refresh_token') : null;
    return this.http
      .post<{ access: string }>(`${this.baseUrl}/token/refresh/`, { refresh })
      .pipe(
        tap((res) => {
          if (this.isBrowser) {
            localStorage.setItem('access_token', res.access);
          }
        })
      );
  }

  // --- Profile ---

  getProfile(): Observable<UserProfile> {
    return this.http.get<UserProfile>(`${this.baseUrl}/profile/`);
  }

  // --- Games ---

  getGames(params?: { status?: string; type?: string; mine?: boolean }): Observable<Game[]> {
    let url = `${this.baseUrl}/games/?`;
    if (params?.status) url += `status=${params.status}&`;
    if (params?.type) url += `type=${params.type}&`;
    if (params?.mine) url += `mine=true&`;
    return this.http.get<Game[]>(url);
  }

  createGame(data: { game_type: string; bot_level?: number; side?: string; time_control?: number }): Observable<Game> {
    return this.http.post<Game>(`${this.baseUrl}/games/`, data);
  }

  getGameById(id: number): Observable<Game> {
    return this.http.get<Game>(`${this.baseUrl}/games/${id}/`);
  }

  getGameMoves(id: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/games/${id}/moves/`);
  }

  getActiveGames(): Observable<Game[]> {
    return this.http.get<Game[]>(`${this.baseUrl}/games/?mine=true&status=IN_PROGRESS`);
  }

  // --- Matchmaking ---

  joinMatchmaking(): Observable<MatchmakingResponse> {
    return this.http.post<MatchmakingResponse>(`${this.baseUrl}/matchmaking/join/`, {});
  }

  leaveMatchmaking(): Observable<any> {
    return this.http.delete(`${this.baseUrl}/matchmaking/leave/`);
  }

  // --- Avatar ---

  uploadAvatar(file: File): Observable<{ avatar: string }> {
    const formData = new FormData();
    formData.append('avatar', file);
    return this.http.patch<{ avatar: string }>(`${this.baseUrl}/profile/avatar/`, formData);
  }

  deleteAvatar(): Observable<{ avatar: null }> {
    return this.http.delete<{ avatar: null }>(`${this.baseUrl}/profile/avatar/`);
  }

  // --- Username ---

  updateUsername(username: string): Observable<{ username: string }> {
    return this.http.patch<{ username: string }>(`${this.baseUrl}/profile/username/`, { username });
  }
}