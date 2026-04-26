"""
Πthon Arena — Server
EECE 350 Computing Networks

Two-player online snake battle game server.
Clients connect over TCP, send JSON commands, and receive JSON game-state broadcasts.
The server runs the full game loop: movement, collision detection, health management,
pie/obstacle logic, spectator support, and in-game text chat relay.

Run:  python server.py <port>
      python server.py 5050
"""

import socket
import threading
import json
import sys
import time
import random

# ─── Constants ────────────────────────────────────────────────────────────────

DEFAULT_PORT   = 5050
GRID_WIDTH     = 25        # 25 columns
GRID_HEIGHT    = 22        # 22 rows
TICK_RATE      = 0.1       # seconds per tick  →  10 ticks / second
GAME_DURATION  = 60        # seconds
MAX_PIES       = 9         # more pies visible on the grid
FREEZE_TICKS   = 0         # freeze removed: pies only add health now

INITIAL_HEALTH = 300

PIE_VALUES = {
    "normal": 5,
    "golden": 5,
    "power":  5,
}

OBSTACLE_DAMAGE = {
    "regular": 10,
    "spike":   10,
}

WALL_DAMAGE = 10
BODY_DAMAGE = 10           # own body or opponent body collision

# Starting snake positions — list of [x, y] cells, head first
P1_START     = [[7, 2], [6, 2], [5, 2], [4, 2], [3, 2], [2, 2], [1, 2], [0, 2]]  # Player 1 starts moving RIGHT
P2_START     = [[17, 19], [18, 19], [19, 19], [20, 19], [21, 19], [22, 19], [23, 19], [24, 19]]  # Player 2 starts moving LEFT
P1_START_DIR = "RIGHT"
P2_START_DIR = "LEFT"

# Fixed obstacles — hardcoded positions spread across the grid,
# deliberately avoiding the corner areas used as spawn zones.
INITIAL_OBSTACLES = [
    {"x":  6, "y":  4, "kind": "regular"},
    {"x": 12, "y":  3, "kind": "spike"},
    {"x": 18, "y":  5, "kind": "regular"},
    {"x":  6, "y": 16, "kind": "spike"},
    {"x": 13, "y": 18, "kind": "regular"},
    {"x": 19, "y": 11, "kind": "spike"},
    {"x":  3, "y": 10, "kind": "regular"},
    {"x": 10, "y":  8, "kind": "regular"},
    {"x": 16, "y": 15, "kind": "spike"},
    {"x": 21, "y":  8, "kind": "regular"},
]

# ─── Shared State ─────────────────────────────────────────────────────────────
# All mutable shared state is protected by `lock`.

lock = threading.Lock()

clients: dict       = {}          # username → socket
spectators: list    = []          # list of spectator sockets

game_state: dict    = {}          # full game state (sent to clients every tick)
current_tick_rate    = TICK_RATE
player_directions   = [P1_START_DIR, P2_START_DIR]   # latest queued direction per player
frozen_ticks        = [0, 0]      # freeze countdown per player (in ticks)
active_players      = [None, None]  # [p1_username, p2_username] during a match
game_running        = False       # True while the game loop is active

# pending_challenges: challenger_username → target_username
pending_challenges: dict = {}
arena_selections: dict = {}   # username → selected arena
setup_matches: dict = {}       # username → {p1, p2, opponent, player_id}
setup_ready: dict = {}         # username → selected setup payload

# ─── Network Helpers ──────────────────────────────────────────────────────────

def send_message(sock: socket.socket, msg: dict) -> None:
    """Encode `msg` as a newline-terminated JSON string and send it to `sock`.
    Errors are swallowed silently — broken connections are handled in the
    client thread's exception handler."""
    try:
        sock.send((json.dumps(msg) + "\n").encode("utf-8"))
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass


def get_live_matches_unlocked() -> list:
    """Return live matches. Called while lock is held."""
    if game_running and active_players[0] and active_players[1]:
        return [{
            "id": "current",
            "players": list(active_players),
            "arena": game_state.get("arena", "Beirut") if game_state else "Beirut",
        }]
    return []


def broadcast_lobby() -> None:
    """Send an updated player-list and live-match list to every connected client."""
    with lock:
        msg  = {"type": "player_list", "players": list(clients.keys()), "matches": get_live_matches_unlocked()}
        socks = list(clients.values())
    for s in socks:
        send_message(s, msg)


def _snapshot():
    """Return a deep copy of the current game_state suitable for broadcasting.
    Acquires the lock internally; never call while the lock is already held."""
    with lock:
        if not game_state:
            return None
        return {
            "type":      "game_state",
            "snakes":    [[list(cell) for cell in snake] for snake in game_state["snakes"]],
            "pies":      [dict(p) for p in game_state["pies"]],
            "obstacles": [dict(o) for o in game_state["obstacles"]],
            "health":    list(game_state["health"]),
            "time_left": game_state["time_left"],
            "frozen":    list(game_state["frozen"]),
            "arena":     game_state.get("arena", "Beirut"),
            "players":   list(active_players),
            "player_styles": dict(game_state.get("player_styles", {})),
            "stats": [dict(x) for x in game_state.get("stats", [{}, {}])],
        }


def broadcast_game_state() -> None:
    """Push the current game state snapshot to both active players and all spectators."""
    snap = _snapshot()
    if snap is None:
        return
    with lock:
        targets = []
        for uname in active_players:
            if uname and uname in clients:
                targets.append(clients[uname])
        targets.extend(list(spectators))   # copy so we don't hold lock while sending
    for s in targets:
        send_message(s, snap)


def broadcast_game_over(winner: str, health: list) -> None:
    """Broadcast the game_over message to players and spectators."""
    with lock:
        stats = [dict(x) for x in game_state.get("stats", [{}, {}])] if game_state else [{}, {}]
    msg = {"type": "game_over", "winner": winner, "health": health, "stats": stats}
    with lock:
        targets = []
        for uname in active_players:
            if uname and uname in clients:
                targets.append(clients[uname])
        targets.extend(list(spectators))
    for s in targets:
        send_message(s, msg)
    print(f"[GAME OVER] winner: {winner}")

# ─── Game Helpers (call within lock unless noted) ─────────────────────────────

def _direction_delta(direction: str) -> tuple:
    """Convert a direction string to a (dx, dy) grid step."""
    return {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}[direction]


def _occupied_cells() -> set:
    """Return the set of all (x, y) cells occupied by snakes, obstacles, or pies.
    Must be called while the lock is held (reads game_state directly)."""
    occupied = set()
    for snake in game_state["snakes"]:
        for cell in snake:
            occupied.add(tuple(cell))
    for o in game_state["obstacles"]:
        occupied.add((o["x"], o["y"]))
    for p in game_state["pies"]:
        occupied.add((p["x"], p["y"]))
    return occupied


def _spawn_pie() -> None:
    """Spawn one new pie on a random empty cell (no-op if MAX_PIES reached).
    Must be called while the lock is held."""
    if len(game_state["pies"]) >= MAX_PIES:
        return
    occupied = _occupied_cells()
    existing_pies = [(p["x"], p["y"]) for p in game_state.get("pies", [])]
    # Keep pies away from each other and one cell away from the grid border.
    # This prevents cluttered pickups and avoids edge-hugging placement.
    empty = [
        (x, y)
        for x in range(1, GRID_WIDTH - 1)
        for y in range(1, GRID_HEIGHT - 1)
        if (x, y) not in occupied
        and all(abs(x - px) + abs(y - py) >= 4 for px, py in existing_pies)
    ]
    if not empty:
        empty = [
            (x, y)
            for x in range(1, GRID_WIDTH - 1)
            for y in range(1, GRID_HEIGHT - 1)
            if (x, y) not in occupied
        ]
    if not empty:
        return
    x, y = random.choice(empty)
    # All pie kinds give +5 health; no kind freezes the opponent.
    kind = random.choices(["normal", "golden", "power"], weights=[7, 2, 1])[0]
    game_state["pies"].append({"x": x, "y": y, "kind": kind})


def _init_game_state(arena="Beirut", player_styles=None):
    """Populate game_state for a fresh match and reset per-game fields.
    Must be called while the lock is held."""
    global game_state
    game_state = {
        "type":      "game_state",
        "snakes":    [[list(c) for c in P1_START], [list(c) for c in P2_START]],
        "pies":      [],
        "obstacles": [dict(o) for o in INITIAL_OBSTACLES],
        "health":    [INITIAL_HEALTH, INITIAL_HEALTH],
        "time_left": GAME_DURATION,
        "frozen":    [False, False],
        "arena":     arena,
        "player_styles": dict(player_styles or {}),
        "stats": [{"pies": 0, "obstacles": 0, "walls": 0}, {"pies": 0, "obstacles": 0, "walls": 0}],
    }
    player_directions[0] = P1_START_DIR
    player_directions[1] = P2_START_DIR
    frozen_ticks[0] = 0
    frozen_ticks[1] = 0
    for _ in range(MAX_PIES):
        _spawn_pie()


def _is_opposite(d1: str, d2: str) -> bool:
    """Return True when d2 is the 180-degree reverse of d1.
    Used to block suicidal direction reversals."""
    return {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}.get(d1) == d2

# ─── Game Loop ────────────────────────────────────────────────────────────────

def game_loop() -> None:
    """Dedicated thread: advances the game one tick every TICK_RATE seconds.

    Each tick:
      1. Decrement freeze counters.
      2. Update time_left.
      3. Move both snakes one cell in their queued direction.
      4. Check all collision types; apply health changes.
      5. Clamp health to [0, 200].
      6. Detect end conditions (health ≤ 0 or time up).
      7. Broadcast updated state; end match if needed.
    """
    global game_running

    tick       = 0
    start_time = time.time()
    winner     = None
    final_health = None

    while True:
        tick_start = time.time()
        tick += 1

        with lock:
            if not game_running:
                break

            # ── 1. Freeze countdown ───────────────────────────────────────
            for i in range(2):
                if frozen_ticks[i] > 0:
                    frozen_ticks[i] -= 1
                game_state["frozen"][i] = frozen_ticks[i] > 0

            # ── 2. Time ───────────────────────────────────────────────────
            elapsed = time.time() - start_time
            game_state["time_left"] = max(0, int(GAME_DURATION - elapsed))

            # ── 3. Move both snakes ───────────────────────────────────────
            new_heads = []
            for i in range(2):
                dx, dy    = _direction_delta(player_directions[i])
                old_head  = game_state["snakes"][i][0]
                new_head  = [old_head[0] + dx, old_head[1] + dy]
                # Prepend new head; drop tail cell → snake length stays constant
                game_state["snakes"][i] = [new_head] + game_state["snakes"][i][:-1]
                new_heads.append(new_head)

            # ── 4. Collision detection ────────────────────────────────────
            for i in range(2):
                hx, hy = new_heads[i]
                opp    = 1 - i

                # Wall collision — push head back to the previous position so the
                # snake doesn't leave the grid; the body is already shifted.
                if hx < 0 or hx >= GRID_WIDTH or hy < 0 or hy >= GRID_HEIGHT:
                    game_state["health"][i] -= WALL_DAMAGE
                    game_state["stats"][i]["walls"] += 1
                    game_state["stats"][i]["obstacles"] += 1
                    # Put the head back inside the grid and force the next direction inward.
                    # This prevents repeated wall hits from ending the round immediately.
                    old_head = list(game_state["snakes"][i][1])
                    safe_x = max(0, min(GRID_WIDTH - 1, old_head[0]))
                    safe_y = max(0, min(GRID_HEIGHT - 1, old_head[1]))
                    game_state["snakes"][i][0] = [safe_x, safe_y]
                    if hx < 0:
                        player_directions[i] = "RIGHT"
                    elif hx >= GRID_WIDTH:
                        player_directions[i] = "LEFT"
                    elif hy < 0:
                        player_directions[i] = "DOWN"
                    elif hy >= GRID_HEIGHT:
                        player_directions[i] = "UP"
                    print(f"[COLLISION] P{i+1} wall → health {game_state['health'][i]}")
                    continue   # skip body/obstacle/pie checks this tick for this player

                # Own-body collision (compare head against every body segment except itself)
                if [hx, hy] in game_state["snakes"][i][1:]:
                    game_state["health"][i] -= BODY_DAMAGE
                    print(f"[COLLISION] P{i+1} own body → health {game_state['health'][i]}")

                # Opponent body collision (includes opponent's head → head-on crash)
                if [hx, hy] in game_state["snakes"][opp]:
                    game_state["health"][i] -= BODY_DAMAGE
                    print(f"[COLLISION] P{i+1} opp body → health {game_state['health'][i]}")

                # Obstacle collision
                for obs in game_state["obstacles"]:
                    if obs["x"] == hx and obs["y"] == hy:
                        dmg = OBSTACLE_DAMAGE[obs["kind"]]
                        game_state["health"][i] -= dmg
                        game_state["stats"][i]["obstacles"] += 1
                        print(f"[COLLISION] P{i+1} {obs['kind']} obstacle → health {game_state['health'][i]}")
                        old_head = list(game_state["snakes"][i][1])
                        game_state["snakes"][i][0] = old_head
                        if player_directions[i] == "UP":
                            player_directions[i] = "DOWN"
                        elif player_directions[i] == "DOWN":
                            player_directions[i] = "UP"
                        elif player_directions[i] == "LEFT":
                            player_directions[i] = "RIGHT"
                        elif player_directions[i] == "RIGHT":
                            player_directions[i] = "LEFT"
                        break  # at most one obstacle per cell

                # Pie pickup
                for pie in list(game_state["pies"]):
                    if pie["x"] == hx and pie["y"] == hy:
                        gain = PIE_VALUES[pie["kind"]]
                        game_state["health"][i] += gain
                        game_state["stats"][i]["pies"] += 1
                        game_state["pies"].remove(pie)
                        print(f"[PIE] P{i+1} {pie['kind']} +{gain} → health {game_state['health'][i]}")
                        _spawn_pie()
                        break  # at most one pie per cell

            # ── 5. Clamp health ───────────────────────────────────────────
            for i in range(2):
                game_state["health"][i] = max(0, min(200, game_state["health"][i]))

            # ── 6. End-condition check ────────────────────────────────────
            h0, h1 = game_state["health"]
            time_up = game_state["time_left"] <= 0
            p1_dead = h0 <= 0
            p2_dead = h1 <= 0

            if p1_dead or p2_dead or time_up:
                if p1_dead and p2_dead:
                    winner = "draw"
                elif p1_dead:
                    winner = active_players[1] or "draw"
                elif p2_dead:
                    winner = active_players[0] or "draw"
                else:   # time up — higher health wins
                    if h0 > h1:
                        winner = active_players[0]
                    elif h1 > h0:
                        winner = active_players[1]
                    else:
                        winner = "draw"
                final_health  = [h0, h1]
                game_running  = False
        # lock released before broadcasting

        # ── 7. Broadcast ─────────────────────────────────────────────────
        if tick % 10 == 0:
            with lock:
                h  = game_state.get("health", [0, 0])
                tl = game_state.get("time_left", 0)
            print(f"[TICK {tick}] health={h} time_left={tl}")

        broadcast_game_state()

        if winner is not None:
            broadcast_game_over(winner, final_health)
            _reset_to_lobby()
            return

        # Sleep for the remainder of the tick to maintain tick rate
        elapsed_tick = time.time() - tick_start
        sleep_time   = current_tick_rate - elapsed_tick
        if sleep_time > 0:
            time.sleep(sleep_time)


def _reset_to_lobby() -> None:
    """Clear active game data and return players to the lobby."""
    global game_state, game_running
    with lock:
        active_players[0] = None
        active_players[1] = None
        game_state         = {}
        game_running       = False
        frozen_ticks[0]    = 0
        frozen_ticks[1]    = 0
    print("[LOBBY] Match ended — players returned to lobby.")
    broadcast_lobby()


def start_game(p1, p2, arena="Beirut", player_styles=None, speed="medium"):
    """Initialise a new match between p1 (Player 1) and p2 (Player 2),
    notify both players of their IDs, and launch the game-loop thread."""
    global game_running, current_tick_rate
    with lock:
        active_players[0] = p1
        active_players[1] = p2
        speed_rates = {"slow": 0.14, "medium": 0.105, "fast": 0.085}
        current_tick_rate = speed_rates.get(str(speed).lower(), 0.11)
        _init_game_state(arena, player_styles)
        game_running = True

    print(f"[GAME START] {p1} (P1) vs {p2} (P2) speed={speed}")

    p1_sock = clients.get(p1)
    p2_sock = clients.get(p2)
    if p1_sock:
        send_message(p1_sock, {"type": "game_start", "player_id": 1, "arena": arena, "players": [p1, p2], "player_styles": player_styles or {}, "speed": speed})
    if p2_sock:
        send_message(p2_sock, {"type": "game_start", "player_id": 2, "arena": arena, "players": [p1, p2], "player_styles": player_styles or {}, "speed": speed})

    threading.Thread(target=game_loop, daemon=True).start()

# ─── Client Handler ───────────────────────────────────────────────────────────

def handle_client(connection: socket.socket, address: tuple) -> None:
    """Per-client thread: reads newline-delimited JSON messages and dispatches them.

    Message types handled:
      join, challenge, accept, input, chat, spectate
    """
    username = None
    buf: str = ""

    print(f"[CONNECT] {address}")
    try:
        connection.settimeout(1.0)
    except OSError:
        pass

    try:
        while True:
            try:
                chunk = connection.recv(4096).decode("utf-8")
            except socket.timeout:
                continue
            if not chunk:
                break   # client closed the connection cleanly

            buf += chunk
            # Process every complete newline-terminated message in the buffer
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    print(f"[ERROR] Bad JSON from {address}: {line!r}")
                    continue

                mtype = msg.get("type")

                # ── CHECK USERNAME ────────────────────────────────────────
                if mtype == "check_username":
                    name = msg.get("username", "").strip()
                    with lock:
                        available = bool(name) and name not in clients
                    if available:
                        send_message(connection, {"type": "username_ok"})
                    else:
                        send_message(connection, {"type": "username_taken"})

                # ── JOIN ──────────────────────────────────────────────────
                elif mtype == "join":
                    name = msg.get("username", "").strip()
                    with lock:
                        # During the setup-page transition, a player may reconnect with
                        # the same username. Replace the old socket instead of rejecting it.
                        reconnecting_for_setup = name in setup_matches
                        reconnecting_for_game = game_running and name in active_players
                        reconnecting = reconnecting_for_setup or reconnecting_for_game
                        taken = (not name) or (name in clients and not reconnecting)
                        if name and reconnecting:
                            clients[name] = connection
                            username = name
                    if taken:
                        send_message(connection, {"type": "username_taken"})
                    else:
                        with lock:
                            username = name
                            clients[username] = connection
                        send_message(connection, {"type": "username_ok"})
                        print(f"[JOIN] {username}")
                        broadcast_lobby()

                # ── SELECT_ARENA ──────────────────────────────────────────
                elif mtype == "select_arena" and username:
                    arena = msg.get("arena", "").strip()
                    if arena:
                        with lock:
                            arena_selections[username] = arena

                # ── CHALLENGE ─────────────────────────────────────────────
                elif mtype == "challenge" and username:
                    target = msg.get("target", "")
                    with lock:
                        target_sock = clients.get(target)
                        if target_sock:
                            pending_challenges[username] = target
                    if target_sock:
                        send_message(target_sock, {"type": "challenged", "by": username})
                    else:
                        send_message(connection, {"type": "error", "message": "Player not found"})

                # ── ACCEPT ────────────────────────────────────────────────
                elif mtype == "accept" and username:
                    challenger = msg.get("target", "")
                    # Validate: challenge exists, challenger still online, no game in progress
                    with lock:
                        valid = (
                            pending_challenges.get(challenger) == username
                            and challenger in clients
                            and active_players[0] is None
                            and active_players[1] is None
                        )
                        if valid:
                            del pending_challenges[challenger]
                    if valid:
                        # Both players now go to setup; the game starts only after both game pages send setup_ready.
                        with lock:
                            setup_matches[challenger] = {"p1": challenger, "p2": username, "opponent": username, "player_id": 1}
                            setup_matches[username] = {"p1": challenger, "p2": username, "opponent": challenger, "player_id": 2}
                            setup_ready.pop(challenger, None)
                            setup_ready.pop(username, None)
                            arena = arena_selections.get(challenger) or arena_selections.get(username) or "Beirut"
                            challenger_sock = clients.get(challenger)
                            accepter_sock = clients.get(username)

                        if challenger_sock:
                            send_message(challenger_sock, {"type": "go_to_arena", "opponent": username, "player_id": 1, "players": [challenger, username], "arena": arena})
                        if accepter_sock:
                            send_message(accepter_sock, {"type": "go_to_setup", "opponent": challenger, "player_id": 2, "players": [challenger, username], "arena": arena})

                            
                    else:
                        send_message(connection, {"type": "error", "message": "Challenge no longer valid"})

                # ── SETUP READY ────────────────────────────────────────────
                elif mtype == "setup_ready" and username:
                    arena = msg.get("arena", "Beirut")
                    colors = msg.get("snake_colors", {})
                    color_name = msg.get("snake_color_name", "")
                    speed = msg.get("speed", "medium")
                    start_now = False
                    start_args = None

                    with lock:
                        match = setup_matches.get(username)
                        if not match:
                            send_message(connection, {"type": "error", "message": "No pending match setup found"})
                            continue

                        p1 = match["p1"]
                        p2 = match["p2"]
                        setup_ready[username] = {
                            "arena": arena,
                            "snake_colors": colors,
                            "snake_color_name": color_name,
                            "speed": speed,
                        }

                        both_ready = p1 in setup_ready and p2 in setup_ready
                        if both_ready and not game_running:
                            selected_arena = setup_ready[p1].get("arena") or setup_ready[p2].get("arena") or "Beirut"
                            player_styles = {
                                p1: setup_ready[p1],
                                p2: setup_ready[p2],
                            }
                            selected_speed = setup_ready[p1].get("speed", "medium")
                            setup_ready.pop(p1, None)
                            setup_ready.pop(p2, None)
                            setup_matches.pop(p1, None)
                            setup_matches.pop(p2, None)
                            start_now = True
                            start_args = (p1, p2, selected_arena, player_styles, selected_speed)

                    if start_now and start_args:
                        start_game(*start_args)
                    else:
                        send_message(connection, {"type": "waiting_for_opponent"})

                # ── INPUT ─────────────────────────────────────────────────
                elif mtype == "input" and username:
                    direction = msg.get("direction", "").upper()
                    if direction not in ("UP", "DOWN", "LEFT", "RIGHT"):
                        continue
                    with lock:
                        idx = None
                        if username == active_players[0]:
                            idx = 0
                        elif username == active_players[1]:
                            idx = 1

                        if idx is not None and not game_state.get("frozen", [False, False])[idx]:
                            # Block 180-degree reversals to prevent instant self-collision
                            if not _is_opposite(player_directions[idx], direction):
                                player_directions[idx] = direction

                # ── CHAT ──────────────────────────────────────────────────
                elif mtype == "chat" and username:
                    text = msg.get("message", "")
                    if not text.strip():
                        continue
                    with lock:
                        # Relay to both active players, including the sender, so chat displays
                        # like a normal conversation on both screens.
                        targets = []
                        for uname in active_players:
                            sock = clients.get(uname) if uname else None
                            if sock and sock not in targets:
                                targets.append(sock)
                    for sock in targets:
                        send_message(sock, {"type": "chat", "from": username, "message": text})

                # ── SPECTATE MATCH LIST ───────────────────────────────
                elif mtype in ("list_matches", "spectate") and username:
                    with lock:
                        matches = get_live_matches_unlocked()
                    send_message(connection, {"type": "matches_list", "matches": matches})

                # ── SPECTATE A SELECTED MATCH ─────────────────────────────
                elif mtype == "spectate_match" and username:
                    match_id = msg.get("match_id", "current")
                    with lock:
                        valid = (match_id == "current" and game_running and active_players[0] and active_players[1])
                        if valid and connection not in spectators:
                            spectators.append(connection)
                        players = list(active_players) if valid else []
                        arena = game_state.get("arena", "Beirut") if valid and game_state else "Beirut"
                        styles = dict(game_state.get("player_styles", {})) if valid and game_state else {}
                    if not valid:
                        send_message(connection, {"type": "error", "message": "No live match to spectate."})
                        continue
                    send_message(connection, {"type": "spectate_start", "match_id": match_id, "players": players, "arena": arena, "player_styles": styles})
                    print(f"[SPECTATE] {username} watching {' vs '.join(players)}")
                    snap = _snapshot()
                    if snap:
                        send_message(connection, snap)

    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        print(f"[ERROR] {username or address}: {e}")

    finally:
        # Determine whether a live game must be ended due to this disconnect
        game_interrupted   = False
        interrupted_winner = None
        interrupted_health = None

        with lock:
            if username:
                if clients.get(username) is connection:
                    clients.pop(username, None)
                arena_selections.pop(username, None)
            if connection in spectators:
                spectators.remove(connection)

            # If the disconnecting client was an active player mid-game, opponent wins by forfeit
            if username and username in active_players and game_running:
                idx      = active_players.index(username)
                opp_idx  = 1 - idx
                opp_name = active_players[opp_idx]
                interrupted_winner = opp_name if opp_name else "draw"
                interrupted_health = list(game_state.get("health", [0, 0]))
                game_interrupted   = True

        if username:
            print(f"[DISCONNECT] {username}")

        if game_interrupted:
            print(f"[DISCONNECT] {username} left mid-game — {interrupted_winner} wins by forfeit")
            broadcast_game_over(interrupted_winner, interrupted_health)
            _reset_to_lobby()

        broadcast_lobby()

        try:
            connection.close()
        except OSError:
            pass

# ─── Entry Point ──────────────────────────────────────────────────────────────

def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow quick server restart without "address already in use" errors
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("", port))
    server_socket.listen(10)
    print(f"[SERVER] Pithon Arena listening on port {port}")

    try:
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
