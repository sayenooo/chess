import { Injectable } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class GameService {
  private socket$!: WebSocketSubject<any>;

  connect(roomName: string, type: 'solo' | 'online' | 'bot' = 'solo'): Observable<any> {
    this.socket$ = webSocket(
      `ws://127.0.0.1:8000/ws/game/${roomName}/?type=${type}`
    );

    return this.socket$.asObservable();
  }

  sendMove(from: string, to: string, promotion?: string): void {
    this.socket$.next({
      action: 'move',
      from_square: from,
      to_square: to,
      ...(promotion ? { promotion } : {})
    });
  }

  getState(): void {
    this.socket$.next({ action: 'get_state' });
  }

  resign(): void {
    this.socket$.next({ action: 'resign' });
  }

  newGame(): void {
    this.socket$.next({ action: 'new_game' });
  }

  disconnect(): void {
    if (this.socket$) {
      this.socket$.complete();
    }
  }
}