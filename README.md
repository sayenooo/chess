# ♟ Chess Project

Шахматный онлайн/оффлайн проект на **Django 6** (backend) + **Angular 21** (frontend).

---

## Стек технологий

| Компонент | Технологии |
|-----------|-----------|
| Backend | Django 6, Django REST Framework, Django Channels, Daphne |
| Frontend | Angular 21 |
| WebSocket | Channels + InMemoryChannelLayer (dev) / Redis (prod) |
| База данных | SQLite (dev) / PostgreSQL (prod) |

---

## 🚀 Запуск проекта

### Backend (Django)

```bash
cd backend

# 1. Активировать виртуальное окружение
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # macOS / Linux

# 2. Установить зависимости (если еще не установлены)
pip install -r requirements.txt

# 3. Применить миграции базы данных
python manage.py migrate

# 4. (Опционально) Создать суперпользователя для админ-панели
python manage.py createsuperuser

# 5. Запустить сервер
python manage.py runserver
```

Сервер запустится на **http://127.0.0.1:8000**.  
Daphne уже настроен, поэтому `runserver` поднимает и HTTP, и WebSocket одновременно.

### Frontend (Angular)

```bash
cd frontend

npm install   # первый раз
npm start     # → http://localhost:4200
```

---

## 🌐 API Endpoints (REST)

Базовый URL: `http://127.0.0.1:8000/api/`

### Игры

| Метод | URL | Описание |
|-------|-----|----------|
| `GET` | `/api/games/` | Список всех игр |
| `GET` | `/api/games/?status=IN_PROGRESS` | Фильтр по статусу |
| `GET` | `/api/games/?type=SOLO` | Фильтр по типу |
| `GET` | `/api/games/{id}/` | Детали конкретной игры |
| `GET` | `/api/games/{id}/moves/` | История ходов партии |
| `POST` | `/api/games/` | Создать новую игру |

### Ходы

| Метод | URL | Описание |
|-------|-----|----------|
| `GET` | `/api/moves/` | Все ходы (все игры) |
| `GET` | `/api/moves/{id}/` | Конкретный ход |

### Админ-панель

| URL | Описание |
|-----|----------|
| `/admin/` | Django Admin (управление Game / Move) |

---

## 🔌 WebSocket API

### Подключение

```
ws://127.0.0.1:8000/ws/game/<room_name>/?type=<тип>
```

| Параметр | Значения | Описание |
|----------|----------|----------|
| `room_name` | любая строка | Уникальный ID комнаты (напр. `solo-1`, `room-42`) |
| `type` | `solo`, `online`, `bot` | Тип игры (по умолчанию `online`) |

**Примеры URL:**
- Solo:   `ws://127.0.0.1:8000/ws/game/my-solo-game/?type=solo`
- Online: `ws://127.0.0.1:8000/ws/game/room-42/?type=online`

### При подключении клиент получает

```json
{
  "type": "game_state",
  "game_type": "SOLO",
  "payload": {
    "board": [
      {"square": "a1", "type": "Rook", "color": "white"},
      {"square": "b1", "type": "Knight", "color": "white"},
      ...
    ],
    "current_turn": "white",
    "move_count": 0,
    "is_check": false
  }
}
```

### Отправка хода (клиент → сервер)

```json
{
  "action": "move",
  "from_square": "e2",
  "to_square": "e4"
}
```

С превращением пешки:
```json
{
  "action": "move",
  "from_square": "e7",
  "to_square": "e8",
  "promotion": "Queen"
}
```

### Ответ на ход (сервер → клиент)

```json
{
  "type": "move_result",
  "payload": {
    "from_square": "e2",
    "to_square": "e4",
    "piece": "Pawn",
    "captured": null,
    "promotion": null,
    "is_check": false,
    "is_checkmate": false,
    "is_stalemate": false,
    "status": "in_progress",
    "board": { "...обновлённое состояние доски..." }
  }
}
```

### Другие действия

| Action | Описание | Пример |
|--------|----------|--------|
| `get_state` | Получить текущее состояние | `{"action": "get_state"}` |
| `resign` | Сдаться | `{"action": "resign"}` |
| `new_game` | Начать новую партию | `{"action": "new_game"}` |

### Ошибки

```json
{
  "type": "error",
  "payload": {
    "message": "Illegal move: e2 → e5",
    "legal_moves": ["e3", "e4"]
  }
}
```

---

## 📬 Тестирование в Postman

### REST API

1. Открой Postman
2. `GET http://127.0.0.1:8000/api/games/` → список игр
3. `POST http://127.0.0.1:8000/api/games/`  
   Body (JSON): `{"game_type": "SOLO"}`  
   → создаст новую игру и вернёт её данные

### WebSocket

Postman поддерживает WebSocket:
1. **New** → **WebSocket**
2. URL: `ws://127.0.0.1:8000/ws/game/test-solo/?type=solo`
3. Нажми **Connect**
4. Получишь начальное состояние доски
5. Отправь ход:
   ```json
   {"action": "move", "from_square": "e2", "to_square": "e4"}
   ```
6. Получишь `move_result` с обновлённой доской
7. Отправь ход чёрных:
   ```json
   {"action": "move", "from_square": "e7", "to_square": "e5"}
   ```

---

## 🎮 Режимы игры

| Режим | Статус | Описание |
|-------|--------|----------|
| **Solo** | ✅ Готов | Один игрок ходит за обе стороны. Подключайся с `?type=solo` |
| **Online** | ✅ Базовый | Два игрока в одной комнате, ходы транслируются обоим |
| **Bot** | 🔜 Планируется | Игра против ИИ |

### Solo-режим

- Подключайся к `ws://127.0.0.1:8000/ws/game/anything/?type=solo`
- Ходи за белых, потом за чёрных (поочерёдно)
- Все ходы сохраняются в БД
- При отключении доска очищается

### Online-режим

- Два клиента подключаются к **одному** `room_name`
- Ходы одного игрока транслируются второму через channel layer
- Сервер не проверяет, кто за белых/чёрных (пока)

---

## 📊 Модели базы данных

### Game

| Поле | Тип | Описание |
|------|-----|----------|
| `game_type` | ONLINE / SOLO / BOT | Тип игры |
| `player_white` | CharField | Имя белого игрока |
| `player_black` | CharField | Имя чёрного игрока |
| `current_fen` | CharField | Текущая позиция (FEN) |
| `status` | WAITING / IN_PROGRESS / CHECKMATE / STALEMATE / DRAW / RESIGNED | Статус |
| `winner` | CharField | Победитель |
| `created_at` | DateTime | Дата создания |
| `last_move_at` | DateTime | Дата последнего хода |

### Move

| Поле | Тип | Описание |
|------|-----|----------|
| `game` | FK → Game | Партия |
| `move_number` | int | Номер хода |
| `from_square` | CharField | Откуда (e2) |
| `to_square` | CharField | Куда (e4) |
| `piece_moved` | CharField | Фигура (Pawn, Knight, ...) |
| `piece_captured` | CharField | Взятая фигура |
| `promotion` | CharField | Превращение |
| `is_check` | bool | Шах |
| `is_checkmate` | bool | Мат |
| `is_stalemate` | bool | Пат |

---

## 🗂 Структура проекта

```
chess-project/
├── backend/
│   ├── backend/              # Django project settings
│   │   ├── settings.py       # Настройки (DB, Channels, CORS)
│   │   ├── urls.py           # Главные URL (/admin, /api)
│   │   └── asgi.py           # ASGI для HTTP + WebSocket
│   ├── game/                 # Основное приложение
│   │   ├── engine/           # Шахматный движок
│   │   │   ├── board.py      # Доска, логика ходов
│   │   │   └── pieces.py     # Фигуры (Pawn, Rook, Knight, ...)
│   │   ├── consumers.py      # WebSocket consumer (solo/online)
│   │   ├── models.py         # Game, Move модели
│   │   ├── serializers.py    # DRF сериализаторы
│   │   ├── views.py          # REST API views
│   │   ├── urls.py           # API URL маршруты
│   │   └── routing.py        # WebSocket URL маршруты
│   ├── db.sqlite3            # База данных
│   ├── manage.py
│   └── requirements.txt
└── frontend/                 # Angular 21
    ├── src/
    └── package.json
```

---

## 🔮 Планы на будущее

- [ ] **Модель Player** — рейтинг (ELO), статистика побед/поражений
- [ ] **Аутентификация** — регистрация, логин, JWT-токены
- [ ] **Matchmaking** — автоматический поиск соперника
- [ ] **Bot-режим** — игра против ИИ (minimax)
- [ ] **Фронтенд** — шахматная доска на Angular
- [ ] **Redis** — channel layer для продакшена
- [ ] **PostgreSQL** — миграция с SQLite

---

## ⚙️ Для фронтенда (Angular)

### Какие события слушать

Фронтенд должен подключаться по WebSocket и обрабатывать следующие `type` в сообщениях:

| `type` | Когда приходит | Что делать |
|--------|---------------|------------|
| `game_state` | При подключении, `get_state`, `new_game` | Отрисовать доску и фигуры |
| `move_result` | После каждого хода | Обновить доску, показать анимацию хода |
| `game_over` | При resign | Показать экран «Игра окончена» |
| `error` | При некорректном ходе | Показать сообщение об ошибке |

### Пример Angular WebSocket сервиса

```typescript
// game.service.ts
import { Injectable } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';

@Injectable({ providedIn: 'root' })
export class GameService {
  private socket$!: WebSocketSubject<any>;

  connect(roomName: string, type: 'solo' | 'online' = 'solo') {
    this.socket$ = webSocket(
      `ws://127.0.0.1:8000/ws/game/${roomName}/?type=${type}`
    );
    return this.socket$.asObservable();
  }

  sendMove(from: string, to: string, promotion?: string) {
    this.socket$.next({
      action: 'move',
      from_square: from,
      to_square: to,
      ...(promotion && { promotion }),
    });
  }

  resign() {
    this.socket$.next({ action: 'resign' });
  }

  newGame() {
    this.socket$.next({ action: 'new_game' });
  }

  disconnect() {
    this.socket$.complete();
  }
}
```
