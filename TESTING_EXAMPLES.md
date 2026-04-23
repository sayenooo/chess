# 🧪 Примеры реальных запросов и решение проблем

## 📋 Содержание
1. [Полный сценарий тестирования](#полный-сценарий-тестирования)
2. [Тестирование каждого режима игры](#тестирование-каждого-режима-игры)
3. [WebSocket тестирование](#websocket-тестирование)
4. [Решение проблем](#решение-проблем)
5. [Требования к серверу](#требования-к-серверу)

---

## 🎯 Полный сценарий тестирования

### Тест 1: Регистрация и вход

**Запрос 1: Регистрация**
```
POST http://localhost:8000/api/register/
Content-Type: application/json

{
  "username": "testplayer1",
  "email": "player1@test.com",
  "password": "SecurePass123"
}
```

**Ожидаемый ответ (201 Created):**
```json
{
  "id": 1,
  "username": "testplayer1",
  "email": "player1@test.com"
}
```

---

**Запрос 2: Вход**
```
POST http://localhost:8000/api/login/
Content-Type: application/json

{
  "username": "testplayer1",
  "password": "SecurePass123"
}
```

**Ожидаемый ответ (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzA1MzIwNDA5LCJpYXQiOjE3MDUyMzQwMDksImp0aSI6IjE3YTc4YThjOGQyODQyODc5YTBhYjU5ZDAxY2YwODA1IiwidXNlcl9pZCI6MX0.xyz...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcwNTMyMDQwOSwiaWF0IjoxNzA1MjM0MDA5LCJqdGkiOiIxN2E3OGE4YzhkMjg0Mjg3OWEwYWI1OWQwMWNmMDgwNSIsInVzZXJfaWQiOjF9.xyz..."
}
```

**💾 Сохраните:**
- `access_token` → используется для всех запросов
- `refresh_token` → используется для обновления токена

---

### Тест 2: Профиль

**Запрос: Получить профиль**
```
GET http://localhost:8000/api/profile/
Authorization: Bearer {access_token}
```

**Ожидаемый ответ (200 OK):**
```json
{
  "id": 1,
  "username": "testplayer1",
  "email": "player1@test.com",
  "player_profile": {
    "rating": 500,
    "bio": "",
    "created_at": "2024-01-15T10:30:00Z",
    "wins": 0,
    "losses": 0,
    "draws": 0,
    "avatar": null
  }
}
```

---

## 🎮 Тестирование каждого режима игры

### 🎯 ТЕСТ: SOLO (Играешь сам с собой)

#### Этап 1: Создание игры

**Запрос:**
```
POST http://localhost:8000/api/games/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "game_type": "SOLO",
  "time_control": 15
}
```

**Ожидаемый ответ (201 Created):**
```json
{
  "id": 1,
  "game_type": "SOLO",
  "status": "IN_PROGRESS",
  "player_white": {
    "id": 1,
    "user": {
      "id": 1,
      "username": "testplayer1"
    },
    "rating": 500
  },
  "player_black": {
    "id": 1,
    "user": {
      "id": 1,
      "username": "testplayer1"
    },
    "rating": 500
  },
  "bot_level": null,
  "current_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "time_control": 15,
  "white_time_remaining": 900.0,
  "black_time_remaining": 900.0,
  "moves": [],
  "winner": null,
  "created_at": "2024-01-15T10:30:00Z",
  "last_move_at": "2024-01-15T10:30:00Z"
}
```

**💾 Сохраните:** `game_id: 1`

---

#### Этап 2: Проверка деталей игры

**Запрос:**
```
GET http://localhost:8000/api/games/1/
Authorization: Bearer {access_token}
```

**Ожидаемый ответ:** Вся информация об игре (как выше)

---

#### Этап 3: WebSocket подключение и ход

**WebSocket подключение:**
```
ws://localhost:8000/ws/game/1/?type=solo
```

**Ожидаемое подключение:**
```json
{
  "type": "connection_established",
  "message": "Connected to SOLO game"
}
```

---

**Отправить ход (e2 → e4):**
```json
{
  "action": "move",
  "from_square": "e2",
  "to_square": "e4"
}
```

**Ожидаемый ответ:**
```json
{
  "type": "game_state",
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "board": [
    ["r", "n", "b", "q", "k", "b", "n", "r"],
    ["p", "p", "p", "p", "p", "p", "p", "p"],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", "P", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    ["P", "P", "P", "P", ".", "P", "P", "P"],
    ["R", "N", "B", "Q", "K", "B", "N", "R"]
  ],
  "last_move": {
    "from_square": "e2",
    "to_square": "e4",
    "piece_moved": "Pawn",
    "notation": "e4",
    "is_check": false,
    "is_checkmate": false
  },
  "white_to_move": false,
  "game_status": "IN_PROGRESS"
}
```

---

#### Этап 4: Получить историю ходов

**Запрос:**
```
GET http://localhost:8000/api/games/1/moves/
Authorization: Bearer {access_token}
```

**Ожидаемый ответ:**
```json
[
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
    "timestamp": "2024-01-15T10:30:05Z",
    "is_check": false,
    "is_checkmate": false,
    "is_stalemate": false,
    "fen_after_move": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
  }
]
```

---

### 🤖 ТЕСТ: BOT (Играешь против компьютера)

#### Этап 1: Создание игры

**Запрос:**
```
POST http://localhost:8000/api/games/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "game_type": "BOT",
  "bot_level": 3,
  "side": "white",
  "time_control": 15
}
```

**Ожидаемый ответ (201 Created):**
```json
{
  "id": 2,
  "game_type": "BOT",
  "status": "IN_PROGRESS",
  "player_white": {
    "id": 1,
    "user": {
      "id": 1,
      "username": "testplayer1"
    },
    "rating": 500
  },
  "player_black": null,
  "bot_level": 3,
  "current_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "time_control": 15,
  "white_time_remaining": 900.0,
  "black_time_remaining": 900.0,
  "moves": [],
  "winner": null,
  "created_at": "2024-01-15T10:30:10Z",
  "last_move_at": "2024-01-15T10:30:10Z"
}
```

**💾 Сохраните:** `bot_game_id: 2`

---

#### Этап 2: WebSocket подключение

**WebSocket подключение:**
```
ws://localhost:8000/ws/game/2/?type=bot
```

---

#### Этап 3: Ваш ход

**Отправить ход:**
```json
{
  "action": "move",
  "from_square": "e2",
  "to_square": "e4"
}
```

**Ожидаемый ответ:**
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

---

#### Этап 4: Ход бота (автоматический)

**Ожидаемый следующий ответ (ход бота):**
```json
{
  "type": "game_state",
  "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
  "last_move": {
    "from_square": "e7",
    "to_square": "e5",
    "piece_moved": "Pawn",
    "notation": "e5"
  },
  "white_to_move": true,
  "game_status": "IN_PROGRESS"
}
```

---

### 🌐 ТЕСТ: ONLINE (Поиск противника)

#### Этап 1: Присоединиться к очереди поиска

**Запрос (Player 1):**
```
POST http://localhost:8000/api/matchmaking/join/
Authorization: Bearer {access_token_player1}
```

**Ожидаемый ответ (ожидание):**
```json
{
  "status": "searching"
}
```

---

**Запрос (Player 2 - новый пользователь):**
```
POST http://localhost:8000/api/register/
Content-Type: application/json

{
  "username": "testplayer2",
  "email": "player2@test.com",
  "password": "SecurePass123"
}
```

**Затем вход:**
```
POST http://localhost:8000/api/login/
Content-Type: application/json

{
  "username": "testplayer2",
  "password": "SecurePass123"
}
```

**Присоединиться к очереди:**
```
POST http://localhost:8000/api/matchmaking/join/
Authorization: Bearer {access_token_player2}
```

**Ожидаемый ответ (игра найдена):**
```json
{
  "status": "game_found",
  "game_id": 3
}
```

**💾 Сохраните:** `online_game_id: 3`

---

#### Этап 2: Оба игрока подключаются

**Player 1 WebSocket:**
```
ws://localhost:8000/ws/game/3/?type=online
```

**Player 2 WebSocket:**
```
ws://localhost:8000/ws/game/3/?type=online
```

---

#### Этап 3: Ход Player 1 (белые)

**Player 1 отправляет:**
```json
{
  "action": "move",
  "from_square": "e2",
  "to_square": "e4"
}
```

**Оба получают:**
```json
{
  "type": "game_state",
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "last_move": {...},
  "white_to_move": false,
  "game_status": "IN_PROGRESS"
}
```

---

#### Этап 4: Ход Player 2 (чёрные)

**Player 2 отправляет:**
```json
{
  "action": "move",
  "from_square": "e7",
  "to_square": "e5"
}
```

**Оба получают:**
```json
{
  "type": "game_state",
  "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
  "last_move": {...},
  "white_to_move": true,
  "game_status": "IN_PROGRESS"
}
```

---

## 🔗 WebSocket тестирование

### Подключение с помощью curl (альтернатива Postman)

```bash
# Linux/Mac
wscat -c "ws://localhost:8000/ws/game/1/?type=solo"

# Windows (PowerShell)
$ws = New-WebSocketClientConnection -Uri "ws://localhost:8000/ws/game/1/?type=solo"
```

---

### Тестирование превращения пешки

**Сценарий:** Белая пешка на e7, ход e7→e8 с превращением в ферзя

**Запрос:**
```json
{
  "action": "move",
  "from_square": "e7",
  "to_square": "e8",
  "promotion": "Queen"
}
```

**Ожидаемый ответ:**
```json
{
  "type": "game_state",
  "fen": "rnbqkbQr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR b KQq - 0 3",
  "last_move": {
    "from_square": "e7",
    "to_square": "e8",
    "piece_moved": "Pawn",
    "promotion": "Queen",
    "notation": "e8=Q"
  },
  "white_to_move": false
}
```

---

### Тестирование рокировки

**Король белых не ходил, ладья не ходила:**

**Запрос (короткая рокировка):**
```json
{
  "action": "move",
  "from_square": "e1",
  "to_square": "g1"
}
```

**Ожидаемый ответ:**
```json
{
  "type": "game_state",
  "last_move": {
    "notation": "O-O",
    "from_square": "e1",
    "to_square": "g1",
    "piece_moved": "King"
  }
}
```

---

### Тестирование шаха

**Запрос (ход, объявляющий шах):**
```json
{
  "action": "move",
  "from_square": "f1",
  "to_square": "c4"
}
```

**Ожидаемый ответ:**
```json
{
  "type": "game_state",
  "last_move": {
    "is_check": true,
    "notation": "Bc4+",
    "from_square": "f1",
    "to_square": "c4"
  }
}
```

---

### Тестирование завершения игры

**Запрос (мат):**
```json
{
  "action": "move",
  "from_square": "d1",
  "to_square": "f7"
}
```

**Ожидаемый ответ (если это мат):**
```json
{
  "type": "game_state",
  "last_move": {
    "is_checkmate": true,
    "notation": "Qxf7#"
  },
  "game_status": "CHECKMATE",
  "winner": {...}
}
```

---

## 🐛 Решение проблем

### ❌ Ошибка 401: Unauthorized

**Причина:** Отсутствует или истёк токен

**Решение:**
```
1. Проверьте, что установлен заголовок:
   Authorization: Bearer {access_token}

2. Если токен истёк, обновите его:
   POST /api/token/refresh/
   Body: {refresh: {refresh_token}}

3. Если не помогло, заново выполните Login:
   POST /api/login/
```

---

### ❌ Ошибка 400: Invalid move

**Причина:** Недопустимый ход в текущей позиции

**Проверьте:**
- Формат квадрата (a1-h8)
- Ход в соответствии с правилами шахмат
- Ладья не может ходить диагонально
- Пешка белых ходит "вверх" (e2→e4), чёрных "вниз" (e7→e5)

**Пример неправильного хода:**
```json
{
  "action": "move",
  "from_square": "e1",
  "to_square": "e5"  // Король не может ходить на 4 клетки!
}
```

---

### ❌ WebSocket не подключается

**Причина 1: Сервер не запущен**
```bash
# Запустите:
python manage.py runserver
```

**Причина 2: Неправильный URL**
```
❌ ws://localhost/ws/game/1/
✅ ws://localhost:8000/ws/game/1/
```

**Причина 3: Не авторизованы**
- WebSocket требует авторизации
- Убедитесь, что выполнили Login перед подключением

---

### ❌ Ошибка 404: Game not found

**Причина:** Game ID не существует

**Проверьте:**
1. Правильно ли скопирован ID:
   ```
   GET /api/games/{{game_id}}/
   ```
2. Игра была создана:
   ```
   GET /api/games/?mine=true
   ```

---

### ❌ Ошибка: "Username already taken"

**Решение:** Используйте уникальный username
```json
{
  "username": "testplayer_" + timestamp
}
```

---

### ⚠️ WebSocket подключился, но нет ответа на ход

**Проверьте:**
1. Отправляется ли JSON корректно?
   ```json
   ✅ {"action": "move", "from_square": "e2", "to_square": "e4"}
   ❌ {action: move, from_square: e2, to_square: e4}
   ```

2. Не ошибка ли в формате квадрата?
   ```
   ✅ e2, a1, h8
   ❌ E2, e2e4, e2-e4
   ```

3. Ходит ли нужная вам сторона?
   - В SOLO вы играете обеими сторонами
   - В BOT/ONLINE только вашей стороной

---

## 📋 Требования к серверу

### Обязательно установить:
```bash
pip install -r requirements.txt
```

### Файл должен содержать:
```
Django>=6.0
djangorestframework>=3.14
djangorestframework-simplejwt>=5.3
daphne>=4.0
channels>=4.0
channels-redis>=4.1
Pillow>=10.0
django-cors-headers>=4.3
```

### Запуск сервера:

**Вариант 1 (обычный):**
```bash
cd backend
python manage.py runserver
```

**Вариант 2 (с Daphne для WebSocket):**
```bash
cd backend
daphne -b 127.0.0.1 -p 8000 backend.asgi:application
```

---

### Проверка конфигурации

**settings.py должен содержать:**
```python
INSTALLED_APPS = [
    'daphne',
    'channels',
    'rest_framework',
    'corsheaders',
    'game',
]

ASGI_APPLICATION = 'backend.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}
```

---

## ✅ Чек-лист тестирования

```
[ ] Регистрация новым пользователем
[ ] Вход и получение токенов
[ ] Получение профиля
[ ] Создание SOLO игры
[ ] WebSocket подключение к SOLO игре
[ ] Ход в SOLO игре (e2→e4)
[ ] Получение истории ходов
[ ] Создание BOT игры (уровень 3)
[ ] Ход против бота
[ ] Ход бота (автоматически)
[ ] Поиск противника (matchmaking)
[ ] Создание ONLINE игры
[ ] Оба игрока подключаются по WebSocket
[ ] Ход первого игрока
[ ] Ход второго игрока
[ ] Превращение пешки
[ ] Завершение игры
[ ] Фильтрация игр
[ ] Обновление username
[ ] Загрузка аватара
```

---

## 📞 Помощь

**Если что-то не работает:**
1. Посмотрите логи сервера: `python manage.py runserver`
2. Проверьте Console в Postman (Ctrl+Alt+C)
3. Убедитесь, что база данных инициализирована: `python manage.py migrate`
4. Перезагрузите сервер
5. Очистите переменные Postman и начните заново
