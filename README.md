# ♟ Chess Project

A full-stack offline and online chess platform built with **Django 6** (backend) and **Angular 21** (frontend).

---

## 🛠 Tech Stack

| Component | Technologies |
|-----------|-----------|
| **Backend** | Django 6, Django REST Framework, Django Channels, Daphne |
| **Frontend** | Angular 21, RxJS |
| **WebSocket** | Channels + InMemoryChannelLayer (dev) / Redis (prod) |
| **Database** | SQLite (dev) / PostgreSQL (prod) |

---

## 🚀 How to Run the Project

### Backend (Django)

```bash
cd backend

# 1. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. (Optional) Create a superuser for the admin panel
python manage.py createsuperuser

# 5. Run the server
python manage.py runserver
```

The server will start at **http://127.0.0.1:8000**.
Daphne is already configured as the ASGI application, so `runserver` starts both HTTP and WebSocket servers simultaneously.

### Frontend (Angular)

```bash
cd frontend

# 1. Install dependencies (first time only)
npm install

# 2. Start the development server
npm start
```
The frontend will be available at **http://localhost:4200**.

---

## 🌐 REST API Endpoints

The base URL for the API is `http://127.0.0.1:8000/api/`

**Authentication uses JWT (JSON Web Tokens). Requests requiring authentication must include the `Authorization: Bearer <token>` header.**

### Authentication & Users
| Method | URL | Description | Accepted JSON | Returned JSON |
|---|---|---|---|---|
| `POST` | `/api/register/` | Register a new user | `{"username": "...", "email": "...", "password": "..."}` | `{"username": "...", "email": "..."}` |
| `POST` | `/api/login/` | Get JWT tokens | `{"username": "...", "password": "..."}` | `{"access": "...", "refresh": "..."}` |
| `POST` | `/api/token/refresh/` | Refresh access token | `{"refresh": "..."}` | `{"access": "..."}` |
| `GET` | `/api/profile/` | Get current user profile | *none* | `{"id": 1, "username": "...", "email": "...", ...}` |

### Matchmaking (Requires Auth)
| Method | URL | Description | Accepted JSON | Returned JSON |
|---|---|---|---|---|
| `POST` | `/api/matchmaking/join/` | Join queue or find game | *none* | `{"status": "game_found", "game_id": 1}` OR `{"status": "searching"}` |
| `DELETE`| `/api/matchmaking/leave/` | Leave the matchmaking queue | *none* | *204 No Content* |

### Games (Requires Auth)
| Method | URL | Description | Accepted JSON | Returned JSON |
|---|---|---|---|---|
| `GET` | `/api/games/` | List all games (Query params: `?status=IN_PROGRESS` or `?type=SOLO`) | *none* | `[{"id": 1, "game_type": "...", "status": "...", ...}]` |
| `GET` | `/api/games/{id}/` | Details of a specific game | *none* | `{"id": 1, "current_fen": "...", "moves": [...], ...}` |
| `POST` | `/api/games/` | Create a new game | `{"game_type": "SOLO|BOT", "bot_level": 1, "side": "white|black|random"}` | Game object details |
| `GET` | `/api/games/{id}/moves/` | Get all moves of a specific game | *none* | `[{"move_number": 1, "from_square": "e2", ...}]` |

### Moves (Read-Only)
| Method | URL | Description |
|---|---|---|
| `GET` | `/api/moves/` | All recorded moves |
| `GET` | `/api/moves/{id}/` | Single move details |

---

## 🔌 WebSocket API

Real-time interactions are handled over WebSockets for game moves, states, and chat features.

### Connection
```
ws://127.0.0.1:8000/ws/game/<room_name>/
```
*(Optionally include query parameters if added in the future, e.g., `?type=solo` is handled internally by checking the game ID).*

**Room Logic:** The `<room_name>` should correspond to the `ID` of the `Game` generated via REST API (`/api/games/` or `/api/matchmaking/join/`).

### Server to Client (What the Frontend receives)

**1. Connection Established**
Triggered right after successful connection:
```json
{
  "type": "connection_established",
  "color": "white",         // Can be "white", "black", or "both" (for SOLO)
  "game_type": "ONLINE"     // "SOLO", "ONLINE", or "BOT"
}
```

**2. Game State**
Triggered when requesting state or initializing a new game:
```json
{
  "type": "game_state",
  "game_type": "SOLO",
  "payload": {
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "current_turn": "white",
    "status": "IN_PROGRESS"
  }
}
```

**3. Move Result**
Triggered whenever a valid move is made by either player (or bot):
```json
{
  "type": "move_result",
  "payload": {
    "from_square": "e2",
    "to_square": "e4",
    "promotion": "Queen",
    "is_check": false,
    "is_checkmate": false,
    "is_stalemate": false,
    "current_turn": "black",
    "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    "legal_moves": [ ["e7", "e5"], ["d7", "d5"] ] // Internal row/col pairs or strings
  }
}
```

**4. Game Over**
Triggered when checkmate, stalemate, or resign occurs:
```json
{
  "type": "game_over",
  "payload": {
    "reason": "checkmate",  // or "stalemate", "resign"
    "winner": "white",
    "resigned_by": "black"  // strictly on resign
  }
}
```

**5. Error**
```json
{
  "type": "error",
  "payload": {
    "message": "Illegal move",
    "details": {}
  }
}
```

### Client to Server (What the Frontend sends)

**1. Make a Move**
```json
{
  "action": "move",
  "from_square": "e2",
  "to_square": "e4",
  "promotion": "Queen" // Optional, default is Queen
}
```

**2. Resign**
```json
{
  "action": "resign"
}
```

**3. Request New Game (Restarts board within same room)**
```json
{
  "action": "new_game"
}
```

**4. Request State**
```json
{
  "action": "get_state"
}
```

---

## 🤝 How Backend and Frontend Communicate (General Workflow)

1. **Authentication:** The frontend gets a JWT token from `/api/login/` and saves it. It sends this token in headers for protected routes.
2. **Setup Game:** 
   - For **Solo/Bot**: The frontend calls `POST /api/games/` to create a new match. The backend returns the `Game ID`.
   - For **Online Multiplayer**: The frontend calls `POST /api/matchmaking/join/` which puts the user in a queue or matches them directly. It returns the `Game ID`.
3. **Connect WebSocket:** The frontend uses the `Game ID` to connect to `ws://127.0.0.1:8000/ws/game/<game_id>/`.
4. **Initialize Board:** Upon connecting, the frontend will receive `connection_established`, and it should send `{"action": "get_state"}` to retrieve the current FEN to render the board properly.
5. **Playing:** 
   - A player moves a piece on UI.
   - Frontend sends `{"action": "move", "from_square": "e2", "to_square": "e4"}`.
   - Backend validates. If legal, saves and broadcasts backwards a `move_result` with updated FEN and game status.
   - Frontend updates board state from FEN or animate piece to the target square.
6. **Game Over:** Handled via the `game_over` WS event or checking `status` fields.

---

## 📊 Database Models

- **User**: Django's built-in user class.
- **Player**: Profile containing rating, bio, stats, linked One-to-One to the User.
- **Game**: Records an active instance. Holds `game_type` (SOLO, ONLINE, BOT), white/black players, current board FEN, winner, and status.
- **Move**: Historic individual turn details. Logs `from_square`, `to_square`, `piece_moved`, and updates statuses (checks/mates). Linked to a `Game`.
- **MatchmakingQueue**: Stores users currently waiting for an online opponent along with their ratings.
