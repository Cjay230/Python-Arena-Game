# The Lebanese Arena

A real-time, two-player snake battle game built with Python, TCP sockets, and Pygame.

---

## About

The Lebanese Arena is an online multiplayer snake game built on a client-server architecture. Two players connect to a central server, challenge each other, and compete in real-time — collecting pies to gain health, dodging obstacles, and outlasting their opponent.

The game is themed around Lebanon, with four iconic arenas to battle in: Beirut, Byblos, Baalbek, and Sidon — each with its own visual backdrop and culturally tied collectible item.

Built as a final project for **EECE 350 – Computing Networks** at the American University of Beirut.

---

## Features

- **TCP Client-Server Architecture** — players connect via IP and port; the server is the single source of truth for all game state
- **Username Validation** — the server rejects duplicate usernames in real time
- **Lobby System** — connected players can see who is online, send challenges, and accept or decline them
- **Arena Selection** — the challenger picks one of four Lebanese-themed arenas; both players load the same environment
- **Snake Customization** — choose a snake color and define custom control keys before each match
- **Pie Collection** — pies spawn dynamically on the board and restore health when collected
- **Rock Obstacles** — fixed obstacles placed by the server damage the snake on impact
- **Collision Detection** — wall hits, snake-on-snake, and obstacle collisions are all computed server-side
- **Timed Matches** — games end after 60 seconds; the player with higher health wins
- **In-Game Chat** — players can exchange messages during the match
- **Spectator Mode** — other connected users can watch live matches without affecting gameplay
- **End Screen Statistics** — final health, pies collected, and obstacles hit are displayed after every match
- **Background Music** — Abu Ali by Ziad Rahbani plays throughout the session
- **Speed Selection** — players select a game speed during setup, applied uniformly by the server

---

## Architecture

The game follows a server-authoritative client-server model.

The **server** runs the game loop, handles all collision detection, spawns pies and obstacles, tracks health, and broadcasts the full game state to both players every tick.

The **client** captures keyboard input, sends movement commands to the server, and renders the received game state using Pygame.

All messages are exchanged as newline-terminated JSON strings over TCP, using a `type` field to distinguish actions (`join`, `challenge`, `accept`, `input`, `chat`, `spectate`, etc.). Multithreading ensures the server handles multiple clients simultaneously without blocking the lobby or ongoing matches.

---

## Project Structure

```
├── server.py               # Main server — connections, game logic, broadcasting
├── client.py               # Main client — GUI, input handling, server communication
├── game.py                 # Pygame rendering — snakes, pies, rocks, health, timer
├── lobby.py                # Lobby screen — player list and challenge flow
├── snake_setup.py          # Snake color and key-binding selection
├── arena_setup.py          # Arena selection screen (challenger only)
├── assets/
│   ├── backgrounds/        # Arena background images
│   ├── music.mp3           # Background music
│   └── ...
└── README.md
```

---

## How to Run

**Requirements**

```bash
pip install pygame
```

Python 3.8 or higher required. No other external dependencies.

**Start the Server**

```bash
python server.py <port>
```

**Start the Client**

```bash
python client.py
```

Enter the server IP address and port on the welcome screen, choose a username, and you are in. Run at least two clients to start a match. A third client may join as a spectator.

---

## Game Flow

```
Welcome Screen  →  Enter username and server IP/port
      ↓
Lobby  →  View online players  →  Send or accept a challenge
      ↓
Arena Selection (challenger)  →  Snake and Controls Setup (both players)
      ↓
Live Match  →  Move, collect pies, avoid rocks and collisions
      ↓
End Screen  →  View final statistics  →  Return to Lobby
```

---

## Team

| Member | Responsibility |
|--------|----------------|
| [Your Name] | Server — game logic, collision detection, multithreading, state broadcasting |
| [Member 2]  | Client — connection flow, lobby, input handling, Pygame rendering |
| [Member 3]  | Design — Lebanese theme, arenas, snake customization, chat, music, spectator mode |

EECE 350 – Computing Networks, Spring 2026
American University of Beirut

---

## License

Developed for academic purposes at AUB. Not intended for commercial use.
