# The Lebanese Arena

A real-time two-player snake battle game built with Python and Pygame, running on a TCP client-server architecture.

---

## Overview

The Lebanese Arena is a networked snake game where two players connect to a central server and compete in live matches. Players collect pies to increase their health, avoid rock obstacles, and try to outlast their opponent before the timer runs out. The player with the higher health at the end wins.

The game is themed around Lebanon, featuring four playable arenas — Beirut, Byblos, Baalbek, and Sidon — each with a distinct background and culturally tied collectible item.

---

## Features

- **Real-time multiplayer** over TCP with a server-authoritative game loop
- **Username validation** — the server rejects duplicate or empty usernames
- **Lobby** — connected players see who is online and can send, accept, or decline challenges
- **Arena selection** — the challenger chooses one of four Lebanese-themed arenas, loaded identically on both sides
- **Snake customization** — players pick a color and define their own four control keys before each match
- **Dynamic pie spawning** — pies appear on the board during the match and restore health on collection
- **Rock obstacles** — static obstacles placed by the server that damage the snake on contact
- **Server-side collision detection** — walls, snake bodies, and obstacles are all handled on the server
- **60-second timed matches** — the higher-health player wins when time runs out
- **In-game chat** — players can send messages to each other during a match
- **Spectator mode** — additional users can join and watch a live match without affecting it
- **Post-match statistics** — final health, pies collected, and obstacles hit are shown on the results screen
- **Speed selection** — players set a preferred game speed during setup, applied uniformly by the server
- **Background music** — Abu Ali by Ziad Rahbani plays throughout the session

---

## Architecture

The server is the single source of truth. It runs the game loop, processes player inputs, handles all collision logic, spawns game objects, and broadcasts the updated game state to all connected clients each tick. Clients are purely responsible for rendering what the server sends and forwarding keyboard input.

All communication is done over TCP using newline-delimited JSON messages. Each message carries a `type` field that tells the receiver how to handle it. Examples include `join`, `challenge`, `accept`, `input`, `chat`, `spectate`, `game_state`, and `game_over`.

The server uses multithreading so that each client is handled on its own thread, keeping the lobby responsive while a match is in progress.

---

## Requirements

- Python 3.8+
- Pygame

```bash
pip install pygame
```

---

## Running the Game

**Start the server:**

```bash
python server.py <port>
```

**Start a client:**

```bash
python client.py
```

On the welcome screen, enter the server's IP address and port number, then choose a username. At least two clients must be connected to start a match. Any additional clients may join as spectators.

---

## Game Flow

```
Welcome Screen  →  Enter username and server connection details
      ↓
Lobby  →  View online players  →  Send or accept a challenge
      ↓
Arena Selection (challenger only)  →  Snake and Controls Setup (both players)
      ↓
Live Match  →  Collect pies, avoid obstacles, outlast your opponent
      ↓
Results Screen  →  View final statistics  →  Return to Lobby
```

---

## Project Structure

```
├── server.py          # Server — client handling, game loop, collision, broadcasting
├── client.py          # Client — connection, input, rendering coordination
├── game.py            # Pygame rendering — grid, snakes, pies, rocks, HUD
├── lobby.py           # Lobby screen — player list, challenge flow
├── snake_setup.py     # Snake color and key-binding configuration
├── arena_setup.py     # Arena selection screen
└── assets/
    ├── backgrounds/   # Arena background images
    └── music.mp3      # Background music
```
