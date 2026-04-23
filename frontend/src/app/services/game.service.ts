import { Injectable, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { Observable, EMPTY } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class GameService {
  private platformId = inject(PLATFORM_ID);
  private socket$!: WebSocketSubject<any>;

  connect(roomName: string): Observable<any> {
    if (!isPlatformBrowser(this.platformId)) return EMPTY;

    const token = localStorage.getItem('access_token') || '';
    const url = `ws://127.0.0.1:8000/ws/game/${roomName}/?token=${token}`;

    this.socket$ = webSocket(url);
    return this.socket$.asObservable();
  }

  sendMove(from: string, to: string, promotion?: string): void {
    this.socket$?.next({
      action: 'move',
      from_square: from,
      to_square: to,
      ...(promotion ? { promotion } : {})
    });
  }

  getState(): void {
    this.socket$?.next({ action: 'get_state' });
  }

  resign(): void {
    this.socket$?.next({ action: 'resign' });
  }

  offerDraw(): void {
    this.socket$?.next({ action: 'offer_draw' });
  }

  respondDraw(accepted: boolean): void {
    this.socket$?.next({ action: 'respond_draw', accepted });
  }

  newGame(): void {
    this.socket$?.next({ action: 'new_game' });
  }

  disconnect(): void {
    if (this.socket$) {
      this.socket$.complete();
    }
  }
}