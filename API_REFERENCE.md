# API Endpoints Reference - Chess Game

## 🔐 Authentication

| Метод | Endpoint | Описание | Body |
|-------|----------|---------|------|
| POST | `/api/register/` | Регистрация | `{username, email, password}` |
| POST | `/api/login/` | Вход | `{username, password}` |
| POST | `/api/token/refresh/` | Обновить токен | `{refresh}` |

**Response (Login):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 👤 Profile

| Метод | Endpoint | Описание | Body | Auth |
|-------|----------|---------|------|------|
| GET | `/api/profile/` | Получить профиль | — | ✅ |
| PATCH | `/api/profile/username/` | Изменить username | `{username}` | ✅ |
| PATCH | `/api/profile/avatar/` | Загрузить аватар | `multipart/form-data` | ✅ |
| DELETE | `/api/profile/avatar/` | Удалить аватар | — | ✅ |

**Response (Profile):**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "player_profile": {
    "rating": 500,
    "bio": "",
    "wins": 0,
    "losses": 0,
    "draws": 0,
    "avatar": null,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## 🎮 Games

| Метод | Endpoint | Описание | Params | Auth |
|-------|----------|---------|--------|------|
| GET | `/api/games/` | Список игр | `mine`, `status`, `type` | ✅ |
| GET | `/api/games/{id}/` | Детали игры | — | ✅ |
| GET | `/api/games/{id}/moves/` | Ходы в игре | — | ✅ |
| POST | `/api/games/` | Создать игру | — | ✅ |

### Создание игры

**SOLO (против себя):**
```json
{
  "game_type": "SOLO",
  "time_control": 15
}
```

**BOT (против компьютера):**
```json
{
  "game_type": "BOT",
  "bot_level": 1-5,
  "side": "white|black|random",
  "time_control": 15
}
```

**ONLINE (поиск противника - смотрите Matchmaking):**
```json
{
  "game_type": "ONLINE",
  "time_control": 15
}
```

### Game Response:
```json
{
  "id": 1,
  "game_type": "SOLO",
  "status": "IN_PROGRESS",
  "player_white": {...},
  "player_black": {...},
  "bot_level": null,
  "current_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "time_control": 15,
  "white_time_remaining": 900,
  "black_time_remaining": 900,
  "moves": [],
  "winner": null,
  "created_at": "2024-01-15T10:30:00Z",
  "last_move_at": "2024-01-15T10:30:00Z"
}
```

### Query Parameters:
```
?mine=true                    # Только мои игры
?status=IN_PROGRESS          # Статус: IN_PROGRESS, CHECKMATE, STALEMATE, DRAW, RESIGNED, WAITING
?type=SOLO                   # Тип: SOLO, BOT, ONLINE
```

**Комбинированные фильтры:**
```
?mine=true&status=IN_PROGRESS&type=SOLO
```

---

## ♟️ Moves

| Метод | Endpoint | Описание | Auth |
|-------|----------|---------|------|
| GET | `/api/moves/` | Все ходы | ✅ |
| GET | `/api/moves/{id}/` | Конкретный ход | ✅ |

**Move Response:**
```json
{
  "id": 1,
  "game": 1,
  "move_number": 1,
  "from_square": "e2",
  "to_square": "e4",
  "piece_moved": "Pawn",
  "piece_captured": "",
  "promotion": "",
  "notation": "e4",
  "is_check": false,
  "is_checkmate": false,
  "is_stalemate": false,
  "fen_after_move": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "timestamp": "2024-01-15T10:30:05Z"
}
```

---

## 🎯 Matchmaking (Online Games)

| Метод | Endpoint | Описание | Auth |
|-------|----------|---------|------|
| POST | `/api/matchmaking/join/` | Присоединиться к очереди | ✅ |
| DELETE | `/api/matchmaking/leave/` | Выйти из очереди | ✅ |

### Join Response:

**Противник найден:**
```json
{
  "status": "game_found",
  "game_id": 42
}
```

**Ожидание поиска:**
```json
{
  "status": "searching"
}
```

### Алгоритм подбора:
1. Проверяет активные ONLINE игры пользователя
2. Ищет противника в диапазоне рейтинга ±100
3. Если найден → создаёт игру, удаляет оба игроков из очереди
4. Если не найден → добавляет в очередь

---

## 🔗 WebSocket

**Connection URL:**
```
ws://localhost:8000/ws/game/{room_name}/?type=solo|online|bot
```

**Room Name:** ID игры (например, `1`, `42`, и т.д.)

### WebSocket Actions

#### 1. Сделать ход
```json
{
  "action": "move",
  "from_square": "e2",
  "to_square": "e4",
  "promotion": "Queen"
}
```

**Параметры:**
- `from_square`: Стартовый квадрат (a1-h8)
- `to_square`: Целевой квадрат (a1-h8)
- `promotion`: (опционально) Queen | Rook | Bishop | Knight

**Response:**
```json
{
  "type": "game_state",
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "last_move": {
    "from_square": "e2",
    "to_square": "e4",
    "piece_moved": "Pawn",
    "notation": "e4"
  },
  "white_to_move": false,
  "game_status": "IN_PROGRESS"
}
```

#### 2. Получить состояние
```json
{
  "action": "get_state"
}
```

#### 3. Сдаться
```json
{
  "action": "resign"
}
```

#### 4. Предложить ничью
```json
{
  "action": "offer_draw"
}
```

---

## 🛠️ HTTP Status Codes

| Код | Значение | Когда возникает |
|-----|----------|-----------------|
| 200 | OK | Успешный GET, DELETE запрос |
| 201 | Created | Успешный POST запрос (создание) |
| 204 | No Content | Успешный DELETE (пустой ответ) |
| 400 | Bad Request | Неверные параметры, валидация ошибка |
| 401 | Unauthorized | Нет токена или токен истёк |
| 403 | Forbidden | Нет доступа к ресурсу |
| 404 | Not Found | Ресурс не найден |
| 500 | Server Error | Ошибка сервера |

---

## 📝 Game Status Values

| Status | Описание |
|--------|---------|
| `WAITING` | Ожидание второго игрока |
| `IN_PROGRESS` | Игра идёт |
| `CHECKMATE` | Шахмат - конец игры |
| `STALEMATE` | Пат - ничья |
| `DRAW` | Ничья |
| `RESIGNED` | Противник сдался |

---

## 🎯 Game Type Values

| Type | Описание |
|------|---------|
| `SOLO` | Играешь сам с собой |
| `BOT` | Играешь против компьютера |
| `ONLINE` | Играешь против другого игрока |

---

## 🤖 Bot Levels

| Level | Сложность |
|-------|-----------|
| 1 | Очень легко |
| 2 | Легко |
| 3 | Средне |
| 4 | Сложно |
| 5 | Очень сложно |

---

## 🎖️ Game Sides

| Side | Описание |
|------|---------|
| `white` | Белые фигуры (ходит первым) |
| `black` | Чёрные фигуры |
| `random` | Случайный выбор |

---

## 🔄 Auth Headers

Для всех защищённых эндпоинтов (те, что отмечены ✅):

```
Authorization: Bearer {access_token}
```

**Пример:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## 📊 Полезные примеры

### Тестовые квадраты доски
```
Ряд 1 (белые): a1, b1, c1, d1, e1, f1, g1, h1
Ряд 2 (пешки): a2, b2, c2, d2, e2, f2, g2, h2
...
Ряд 8 (чёрные): a8, b8, c8, d8, e8, f8, g8, h8
```

### Классические дебюты
- **e2→e4** (King's Pawn Opening)
- **d2→d4** (Queen's Pawn Opening)
- **c2→c4** (English Opening)

### Превращение пешки
- Белая пешка: e7 → e8
- Чёрная пешка: e2 → e1

---

## 🚀 Быстрый старт

```bash
# 1. Регистрация
POST /api/register/
{username, email, password}

# 2. Вход
POST /api/login/
{username, password}
→ Сохранить access_token

# 3. Создать SOLO игру
POST /api/games/
{game_type: "SOLO", time_control: 15}
→ Сохранить game_id

# 4. Подключиться по WebSocket
ws://localhost:8000/ws/game/{game_id}/?type=solo

# 5. Сделать ход
{action: "move", from_square: "e2", to_square: "e4"}

# 6. Получить ходы
GET /api/games/{game_id}/moves/
```

---

## 📞 Debugging

### Логирование в Postman
- Console: Ctrl+Alt+C
- Смотрите вывод test-скриптов
- Проверяйте значения переменных

### Проверка токена
```json
{
  "Authorization": "Bearer {{access_token}}"
}
```

### WebSocket соединение
1. Откройте WebSocket запрос
2. Нажмите **Connect**
3. Смотрите статус подключения
4. Отправляйте JSON в поле **Message**
