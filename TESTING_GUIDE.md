# 🎯 Инструкция по тестированию Chess API в Postman

## 📋 Содержание
1. [Импорт Collection](#импорт-collection)
2. [Переменные окружения](#переменные-окружения)
3. [Пошаговый гайд по тестированию](#пошаговый-гайд-по-тестированию)
4. [WebSocket примеры](#websocket-примеры)
5. [Возможные ошибки](#возможные-ошибки)

---

## 📥 Импорт Collection

### Способ 1: Через URL
1. В Postman нажмите **File** → **Import**
2. Перейдите на вкладку **Link**
3. Скопируйте путь к файлу: `Postman_Collection.json`
4. Нажмите **Import**

### Способ 2: Через файл
1. В Postman нажмите **File** → **Import**
2. Перейдите на вкладку **Upload Files**
3. Выберите файл `Postman_Collection.json`
4. Нажмите **Import**

---

## ⚙️ Переменные окружения

Переменные уже включены в Collection. Проверьте их значения:

```json
{
  "base_url": "http://localhost:8000",      // URL вашего бэкенда
  "access_token": "",                       // Заполняется при логине
  "refresh_token": "",                      // Заполняется при логине
  "user_id": "",                            // Заполняется при получении профиля
  "solo_game_id": "",                       // Заполняется при создании SOLO игры
  "bot_game_id": "",                        // Заполняется при создании BOT игры
  "online_game_id": ""                      // Заполняется при подборе противника
}
```

### Если `base_url` другой:
- Откройте **Environments** → выберите переменные
- Измените `base_url` на ваш адрес (например, `http://127.0.0.1:8000`)

---

## 📝 Пошаговый гайд по тестированию

### Этап 1️⃣: Авторизация

#### Шаг 1: Регистрация
```
POST /api/register/
Body: {
  "username": "testuser1",
  "email": "test1@example.com",
  "password": "TestPassword123"
}
```

**Ожидаемый результат:**
```json
{
  "id": 1,
  "username": "testuser1",
  "email": "test1@example.com"
}
```

#### Шаг 2: Вход (Получить токены)
```
POST /api/login/
Body: {
  "username": "testuser1",
  "password": "TestPassword123"
}
```

**Ожидаемый результат:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Проверка:** Токены должны автоматически сохраниться в переменные благодаря test-скриптам.

---

### Этап 2️⃣: Профиль

#### Шаг 1: Получить профиль
```
GET /api/profile/
Headers:
  Authorization: Bearer {{access_token}}
```

**Ожидаемый результат:**
```json
{
  "id": 1,
  "username": "testuser1",
  "email": "test1@example.com",
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

#### Шаг 2: Изменить username
```
PATCH /api/profile/username/
Body: {
  "username": "newusername123"
}
```

#### Шаг 3: Загрузить аватар (опционально)
```
PATCH /api/profile/avatar/
Body: Form-data
  avatar: [выберите файл .jpg]
```

---

### Этап 3️⃣: SOLO игра (против себя)

#### Шаг 1: Создать SOLO игру
```
POST /api/games/
Body: {
  "game_type": "SOLO",
  "time_control": 15
}
```

**Ожидаемый результат:**
```json
{
  "id": 1,
  "game_type": "SOLO",
  "status": "IN_PROGRESS",
  "current_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "player_white": {...},
  "player_black": {...},
  "moves": [],
  ...
}
```

**Сохранится в переменных:**
- `solo_game_id` 
- `solo_room_name`

#### Шаг 2: Получить детали игры
```
GET /api/games/{{solo_game_id}}/
```

#### Шаг 3: Подключиться по WebSocket и сделать ход
Смотрите раздел [WebSocket примеры](#websocket-примеры)

---

### Этап 4️⃣: BOT игра (против компьютера)

#### Шаг 1: Создать BOT игру (уровень сложности 1-5)
```
POST /api/games/
Body: {
  "game_type": "BOT",
  "bot_level": 3,
  "side": "white",          // или "black", или "random"
  "time_control": 15
}
```

**Уровни сложности:**
- 1 = Очень легко
- 2 = Легко
- 3 = Средне
- 4 = Сложно
- 5 = Очень сложно

#### Шаг 2: Получить детали BOT игры
```
GET /api/games/{{bot_game_id}}/
```

#### Шаг 3: Получить историю ходов
```
GET /api/games/{{bot_game_id}}/moves/
```

#### Шаг 4: Подключиться по WebSocket
Используйте `{{bot_room_name}}` для WebSocket подключения

---

### Этап 5️⃣: ONLINE игра (поиск противника)

#### Шаг 1: Присоединиться к очереди поиска
```
POST /api/matchmaking/join/
Headers:
  Authorization: Bearer {{access_token}}
```

**Возможные ответы:**

A) Противник найден:
```json
{
  "status": "game_found",
  "game_id": 42
}
```
→ Game ID сохранится в `online_game_id`

B) Поиск продолжается:
```json
{
  "status": "searching"
}
```
→ Повторите запрос через несколько секунд

#### Шаг 2: Выйти из очереди (если нужно)
```
DELETE /api/matchmaking/leave/
Headers:
  Authorization: Bearer {{access_token}}
```

#### Шаг 3: Получить детали найденной игры
```
GET /api/games/{{online_game_id}}/
```

#### Шаг 4: Подключиться и играть
Используйте `{{online_room_name}}` для WebSocket подключения

---

### Этап 6️⃣: Фильтрация игр

#### Получить только свои игры
```
GET /api/games/?mine=true
```

#### Получить только активные игры
```
GET /api/games/?status=IN_PROGRESS
```

#### Получить только SOLO игры
```
GET /api/games/?type=SOLO
```

#### Комбинированный фильтр
```
GET /api/games/?mine=true&status=IN_PROGRESS&type=BOT
```

---

## 🔗 WebSocket примеры

### Как подключиться в Postman

1. **Откройте WebSocket запрос** (например, "SOLO - Move")
2. Нажмите кнопку **Connect**
3. Подождите, пока подключение установится
4. В поле **Message** введите JSON и нажмите **Send**

### Пример 1: Простой ход в SOLO

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
  "white_to_move": false
}
```

### Пример 2: Превращение пешки

```json
{
  "action": "move",
  "from_square": "e7",
  "to_square": "e8",
  "promotion": "Queen"
}
```

**Доступные фигуры для превращения:**
- `"Queen"` (по умолчанию)
- `"Rook"`
- `"Bishop"`
- `"Knight"`

### Пример 3: Получить состояние игры

```json
{
  "action": "get_state"
}
```

**Ответ содержит:**
```json
{
  "type": "game_state",
  "fen": "...",
  "board": [...],
  "last_move": {...},
  "white_to_move": true,
  "game_status": "IN_PROGRESS"
}
```

### Пример 4: Сдаться

```json
{
  "action": "resign"
}
```

### Пример 5: Предложить ничью

```json
{
  "action": "offer_draw"
}
```

---

## 🐛 Возможные ошибки

### 1. `401 Unauthorized`
**Причина:** Токен истёк или не установлен
**Решение:** 
- Заново выполните Login запрос
- Убедитесь, что `access_token` в переменных заполнен

### 2. `403 Forbidden`
**Причина:** Нет прав доступа
**Решение:**
- Проверьте, что вы авторизованы
- Убедитесь, что пытаетесь получить доступ к своим играм

### 3. `400 Bad Request - "Username already taken"`
**Причина:** Username уже зарегистрирован
**Решение:** Измените username на уникальный

### 4. `404 Not Found`
**Причина:** Игра или ход не найдены
**Решение:**
- Проверьте ID игры
- Убедитесь, что игра существует

### 5. WebSocket не подключается
**Причина:** Сервер не запущен или WebSocket не активен
**Решение:**
- Запустите сервер: `python manage.py runserver`
- Проверьте, что используется правильный URL

### 6. `Invalid move` (в WebSocket)
**Причина:** Недопустимый ход
**Решение:**
- Проверьте формат квадрата (a1-h8)
- Убедитесь, что ход легален в текущей позиции

---

## 📊 Рекомендуемый порядок тестирования

```
1. Register              → получить пользователя
2. Login                 → получить токены ✅ автосохранение
3. Get Profile           → проверить профиль ✅ автосохранение user_id
4. Create SOLO Game      → создать игру ✅ автосохранение game_id
5. WebSocket (SOLO)      → сделать ход
   ├─ Connect
   ├─ Send move: e2→e4
   └─ Observe response
6. Create BOT Game       → создать игру с ботом
7. WebSocket (BOT)       → играть против бота
8. Join Matchmaking      → поиск противника
9. WebSocket (ONLINE)    → играть онлайн (если нашёлся противник)
```

---

## 💡 Полезные советы

### Автоматические переменные
В Collection настроены автоматические сохранения важных данных:
- Login → автосохраняет `access_token`, `refresh_token`
- Get Profile → автосохраняет `user_id`
- Create Game → автосохраняет `game_id`, `room_name`

### Быстрое тестирование
1. Регистрируйтесь с разными usernames для каждого теста
2. Используйте временные переменные для параллельного тестирования
3. Группируйте запросы в папках (как в Collection)

### Debug режим
1. Откройте **Console** (Ctrl+Alt+C)
2. Смотрите логи запросов и ответов
3. Проверяйте значения переменных в **Environments**

---

## 🎮 Примеры шахматных ходов

Стандартные позиции доски: a1-h8
```
  a b c d e f g h
8 ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜ 8
7 ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟ 7
6 . . . . . . . . 6
5 . . . . . . . . 5
4 . . . . . . . . 4
3 . . . . . . . . 3
2 ♙ ♙ ♙ ♙ ♙ ♙ ♙ ♙ 2
1 ♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖ 1
  a b c d e f g h
```

### Открытия для тестирования:
- **Italian Game**: e2→e4, e7→e5, g1→f3, b8→c6, f1→c4, f8→c5
- **French Defense**: e2→e4, e7→e6, d2→d4, d7→d5
- **Ruy Lopez**: e2→e4, e7→e5, g1→f3, b8→c6, f1→b5

---

## 📞 Контакты для поддержки

Если возникают проблемы:
1. Проверьте логи сервера: `python manage.py runserver`
2. Убедитесь, что всё установлено: `pip install -r requirements.txt`
3. Проверьте миграции: `python manage.py migrate`
