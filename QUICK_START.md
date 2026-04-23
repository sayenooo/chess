# ⚡ Быстрый старт тестирования

## 🚀 За 5 минут до первого теста

### Шаг 1: Подготовка сервера (2 минуты)

```bash
# Перейдите в папку backend
cd backend

# Убедитесь, что все зависимости установлены
pip install -r requirements.txt

# Запустите миграции (если ещё не запущены)
python manage.py migrate

# Запустите сервер
python manage.py runserver
```

**Вы должны увидеть:**
```
Starting development server at http://127.0.0.1:8000/
```

---

### Шаг 2: Импорт в Postman (2 минуты)

1. Откройте **Postman**
2. Нажмите **File** → **Import**
3. Выберите файл **`Postman_Collection.json`** (из корня проекта)
4. Нажмите **Import**

**Готово!** Все 50+ запросов загружены и готовы к использованию.

---

### Шаг 3: Первый тест (1 минута)

1. Откройте папку **"1. AUTHENTICATION"**
2. Нажмите на **"Register - Create Account"**
3. Нажмите **Send**

**Если вы видите статус 201 Created** ✅ - всё работает!

---

## 📋 Рекомендуемый порядок тестирования

### Минимальный тест (5 минут)

```
1. Register
   └─ Создаёт пользователя

2. Login  
   └─ Получает токены

3. Get Profile
   └─ Проверяет профиль

4. Create SOLO Game
   └─ Создаёт игру

5. Get Game Details
   └─ Проверяет игру
```

### Полный тест (20 минут)

```
A. AUTHENTICATION (2 мин)
   1. Register
   2. Login ← сохраняет токены
   3. Get Profile ← сохраняет user_id

B. SOLO GAME (5 мин)
   4. Create SOLO Game ← сохраняет game_id
   5. Get Game Details
   6. WebSocket SOLO (подключение)
   7. WebSocket SOLO (ход e2→e4)
   8. Get Moves

C. BOT GAME (5 мин)
   9. Create BOT Game
   10. Get BOT Game Details
   11. WebSocket BOT (подключение)
   12. WebSocket BOT (ход)

D. ONLINE GAME (5 мин)
   13. Register второй пользователь (повторить A)
   14. Join Matchmaking (Player 1)
   15. Join Matchmaking (Player 2) ← будут найдены друг другом
   16. Get Online Game Details
   17. WebSocket ONLINE (оба подключены)
   18. WebSocket (ходы)

E. ФИЛЬТРЫ (2 мин)
   19. List My Games
   20. List In-Progress Games
   21. Combined Filter
```

---

## 🎯 Чек-лист перед тестированием

```
✅ Python 3.8+           → python --version
✅ pip установлен        → pip --version
✅ Зависимости установлены → pip list | grep django
✅ Миграции выполнены     → python manage.py migrate (если новая БД)
✅ Сервер запущен        → http://localhost:8000
✅ Postman установлен    → Открыть приложение
✅ Collection импортирована → Видите папки в Postman
```

---

## 📂 Файлы для тестирования

Все файлы находятся в корне проекта:

```
chess/
├── Postman_Collection.json      ← Основной файл (импортируйте его!)
├── TESTING_GUIDE.md             ← Подробная инструкция
├── API_REFERENCE.md             ← Справочник всех эндпоинтов
├── TESTING_EXAMPLES.md          ← Реальные примеры запросов
├── QUICK_START.md               ← Этот файл
└── backend/
    ├── manage.py
    ├── requirements.txt
    └── db.sqlite3
```

---

## 🔑 Переменные Postman

Все переменные уже настроены и будут заполняться автоматически:

```
base_url         → http://localhost:8000
access_token     → Заполнится при Login
refresh_token    → Заполнится при Login
user_id          → Заполнится при Get Profile
solo_game_id     → Заполнится при Create SOLO Game
bot_game_id      → Заполнится при Create BOT Game
online_game_id   → Заполнится при Join Matchmaking
```

**Проверить переменные:**
1. Откройте **Environments** в правом верхнем углу
2. Выберите переменные
3. Смотрите текущие значения

---

## 🧪 Мини-тесты по 30 секунд

### Тест 1: Регистрация работает?

```
POST /api/register/
{
  "username": "quicktest_" + timestamp,
  "email": "test@test.com",
  "password": "Test123"
}
```

**Результат:** 201 Created ✅

---

### Тест 2: Авторизация работает?

```
POST /api/login/
{
  "username": "quicktest_...",
  "password": "Test123"
}
```

**Результат:** 200 OK, получены токены ✅

---

### Тест 3: Создание SOLO игры работает?

```
POST /api/games/
Authorization: Bearer {access_token}
{
  "game_type": "SOLO",
  "time_control": 15
}
```

**Результат:** 201 Created, game_id > 0 ✅

---

### Тест 4: WebSocket работает?

```
ws://localhost:8000/ws/game/{game_id}/?type=solo
```

**Результат:** Зелёный статус "Connected" ✅

---

### Тест 5: Ход работает?

```
{
  "action": "move",
  "from_square": "e2",
  "to_square": "e4"
}
```

**Результат:** Получен ответ с новой FEN позицией ✅

---

## 🎮 Примеры реальных ходов

### Часть 1: Итальянская игра

```
1. e2→e4     (e4)
2. e7→e5     (e5)
3. g1→f3     (Nf3)
4. b8→c6     (Nc6)
5. f1→c4     (Bc4)
6. f8→c5     (Bc5)
7. e1→g1     (O-O - короткая рокировка)
```

### Часть 2: Французская защита

```
1. e2→e4     (e4)
2. e7→e6     (e6)
3. d2→d4     (d4)
4. d7→d5     (d5)
5. e4→d5     (exd5)
6. e6→d5     (exd5)
```

---

## 📊 Статусы и коды ошибок

### Успешные коды

```
200 OK              - Запрос успешен, есть результат
201 Created         - Ресурс создан
204 No Content      - Успешно удалено (пустой ответ)
```

### Коды ошибок

```
400 Bad Request     - Неверные параметры (проверьте JSON)
401 Unauthorized    - Отсутствует токен (выполните Login)
403 Forbidden       - Нет доступа к ресурсу
404 Not Found       - Ресурс не существует
500 Server Error    - Ошибка на сервере
```

---

## 🐛 Если что-то не работает

### 1. Проверьте логи сервера

```bash
# В терминале, где запущен сервер:
python manage.py runserver

# Смотрите:
[15/Jan/2024 10:30:00] "POST /api/register/ HTTP/1.1" 201 Created
```

### 2. Проверьте Console в Postman

```
Ctrl + Alt + C (Windows/Linux)
Cmd + Alt + C (Mac)
```

Смотрите тесты и логирование.

### 3. Перезагрузите

```bash
# Остановите сервер (Ctrl+C)
# Запустите заново
python manage.py runserver
```

### 4. Очистите данные

```bash
# Удалите БД
rm backend/db.sqlite3

# Пересоздайте
python manage.py migrate
python manage.py runserver
```

---

## 🌐 URLs для быстрого доступа

```
Backend API:        http://localhost:8000/api/
Admin interface:    http://localhost:8000/admin/
REST Framework:     http://localhost:8000/api/
Database:           backend/db.sqlite3
```

---

## 💾 Сохранение результатов тестирования

### Экспортировать отчёт из Postman

1. Откройте **Collection**
2. Нажмите **⋯** (три точки)
3. Выберите **Export**
4. Сохраните как `chess-api-tests.json`

### Сохранить логи консоли

```bash
# Перенаправьте в файл
python manage.py runserver > server.log 2>&1
```

---

## 📝 Шаблон для документирования теста

```markdown
## Тест: [Название]

**URL:** [эндпоинт]
**Метод:** GET/POST/PATCH/DELETE

**Запрос:**
```json
{...}
```

**Ожидаемый результат:**
```json
{...}
```

**Статус:** 200/201/400/etc

**Дата:** 2024-01-15
**Результат:** ✅ Пройден / ❌ Не пройден
**Заметки:** [если есть проблемы]
```

---

## 🎬 Видео-шаги (текст для документации)

### Шаг 1: Регистрация
1. Откройте "1. AUTHENTICATION" → "Register"
2. Измените username на уникальный
3. Нажмите Send
4. Результат: 201 Created

### Шаг 2: Вход
1. Откройте "1. AUTHENTICATION" → "Login"
2. Используйте тот же username/password
3. Нажмите Send
4. Результат: 200 OK + получены токены

### Шаг 3: Создание SOLO игры
1. Откройте "3. GAMES - SOLO" → "Create SOLO Game"
2. Нажмите Send
3. Результат: 201 Created + сохранён game_id

### Шаг 4: WebSocket подключение
1. Откройте "8. WEBSOCKET" → "SOLO - Move"
2. Нажмите Connect
3. В поле Message вставьте:
   ```json
   {"action": "move", "from_square": "e2", "to_square": "e4"}
   ```
4. Нажмите Send
5. Результат: Получена новая позиция

---

## 🎯 Успешный тест = зелёные статусы

```
✅ 201 Created       → Ресурс создан
✅ 200 OK            → Данные получены
✅ Connected         → WebSocket подключён
✅ Ответ JSON        → Валидный формат
✅ Значения заполнены → Переменные сохранены
```

---

## 🚨 Типичные ошибки и решения

| Ошибка | Причина | Решение |
|--------|---------|---------|
| 401 Unauthorized | Нет токена | Выполните Login |
| 400 Bad Request | JSON ошибка | Проверьте синтаксис |
| 404 Not Found | ID не существует | Проверьте ID игры |
| Cannot connect WebSocket | Сервер не запущен | `python manage.py runserver` |
| Invalid move | Ход недопустимый | Используйте легальный ход |

---

## 📞 Поддержка

**Если понадобилась помощь:**
1. Прочитайте `TESTING_GUIDE.md` для подробностей
2. Смотрите `TESTING_EXAMPLES.md` для примеров
3. Проверьте `API_REFERENCE.md` для всех эндпоинтов
4. Посмотрите логи сервера и Console Postman

---

## ✨ Готово!

Вы готовы тестировать Chess API! 🎉

**Начните с:**
```
1. Запустить сервер
2. Импортировать Postman Collection
3. Нажать на "Register"
4. Нажать Send
5. Смотреть результаты
```

**Удачи в тестировании!** 🚀
