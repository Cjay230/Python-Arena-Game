import socket
import json
import threading


class GameClient: #client state
    def __init__(self):
        self.sock = None
        self.running = False
        # Data that the GUI can use later
        self.username = ""
        self.connected = False
        self.player_list = []
        self.last_challenge_from = None #Stores who challenged this player.
        self.game_started = False
        self.player_id = None
        self.game_state = None #stores fata from server
        self.game_over = False
        self.winner = None
        self.final_health = None
        self.spectating = False
        self.chat_messages = []
        self.last_error = None
        self.challenge_target = None
        self.player_names = []
        self.go_to_setup = False
        self.go_to_arena = False
        self.opponent = None
        self.waiting_for_opponent = False
        self.player_styles = {}
        self.final_stats = None
        self.speed = "medium"
        self.matches = []
        self.selected_match_id = None

    def connect(self, host, port): #connect client to the server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create TCP socket
        self.sock.settimeout(4.0)
        self.sock.connect((host, port)) #connects to the server at the given IP and port
        self.sock.settimeout(1.0)
        self.running = True #marks client as active

    def send_message(self, data): #send one JSON message to the server
        msg = json.dumps(data) + "\n"
        self.sock.sendall(msg.encode())

    def join(self, username): #send join request to server
        self.username = username
        self.send_message({
            "type": "join",
            "username": username
        })

    def challenge(self, target): #send challenge request to palyer2
        self.challenge_target = target
        self.send_message({
            "type": "challenge",
            "target": target
        })

    def accept(self, target):  #Accept a challenge
        self.last_challenge_from = target
        self.send_message({
            "type": "accept",
            "target": target
        })

    def move(self, direction): #send movement input
        self.send_message({
            "type": "input",
            "direction": direction.upper()
        })

    def send_chat(self, text): #send chat message
        self.send_message({
            "type": "chat",
            "message": text
        })

    def request_matches(self):
        self.send_message({"type": "list_matches"})

    def spectate_match(self, match_id):
        self.selected_match_id = match_id
        self.send_message({
            "type": "spectate_match",
            "match_id": match_id
        })

    def spectate(self):
        self.request_matches()

    def setup_ready(self, arena, snake_colors=None, snake_color_name="", speed="medium"):
        self.waiting_for_opponent = True
        self.send_message({
            "type": "setup_ready",
            "arena": arena,
            "snake_colors": snake_colors or {},
            "snake_color_name": snake_color_name,
            "speed": speed
        })

    def handle_message(self, msg): #update client state based on server message
        mtype = msg.get("type")

        if mtype == "username_ok":
            self.connected = True

        elif mtype == "username_taken":
            self.connected = False
            self.last_error = "Username already taken"

        elif mtype == "player_list":
            self.player_list = msg.get("players", [])
            self.matches = msg.get("matches", getattr(self, "matches", []))

        elif mtype == "challenged":
            self.last_challenge_from = msg.get("by")
        elif mtype == "go_to_arena":
            self.go_to_arena = True
            self.opponent = msg.get("opponent")
            self.player_id = msg.get("player_id", self.player_id)
            self.arena = msg.get("arena", getattr(self, "arena", "Beirut"))
            players = msg.get("players")
            if isinstance(players, list) and len(players) >= 2:
                self.player_names = players

        elif mtype == "go_to_setup":
            self.go_to_setup = True
            self.opponent = msg.get("opponent")
            self.player_id = msg.get("player_id", self.player_id)
            self.arena = msg.get("arena", getattr(self, "arena", "Beirut"))
            players = msg.get("players")
            if isinstance(players, list) and len(players) >= 2:
                self.player_names = players

        elif mtype == "waiting_for_opponent":
            self.waiting_for_opponent = True

        elif mtype == "game_start":
            self.waiting_for_opponent = False
            self.game_started = True
            self.game_over = False
            self.player_id = msg.get("player_id")
            names = msg.get("players")
            if isinstance(names, list) and len(names) >= 2:
                self.player_names = names
            elif self.player_id == 1 and self.challenge_target:
                self.player_names = [self.username, self.challenge_target]
            elif self.player_id == 2 and self.last_challenge_from:
                self.player_names = [self.last_challenge_from, self.username]
            self.arena = msg.get("arena", getattr(self, "arena", "Beirut"))
            self.player_styles = msg.get("player_styles", getattr(self, "player_styles", {}))
            self.speed = msg.get("speed", getattr(self, "speed", "medium"))

        elif mtype == "game_state":
            if self.player_names and "players" not in msg:
                msg["players"] = self.player_names
            if "player_styles" in msg:
                self.player_styles = msg.get("player_styles", {})
            self.game_state = msg

        elif mtype == "game_over":
            self.game_started = False
            self.game_over = True
            self.winner = msg.get("winner")
            self.final_health = msg.get("health")
            self.final_stats = msg.get("stats")

        elif mtype == "chat":
            sender = msg.get("from")
            text = msg.get("message")
            self.chat_messages.append((sender, text))

        elif mtype == "matches_list":
            self.matches = msg.get("matches", [])

        elif mtype == "spectate_start":
            self.spectating = True
            self.game_started = True
            self.game_over = False
            self.player_id = 0
            names = msg.get("players", [])
            if isinstance(names, list) and len(names) >= 2:
                self.player_names = names
            self.arena = msg.get("arena", getattr(self, "arena", "Beirut"))
            self.player_styles = msg.get("player_styles", getattr(self, "player_styles", {}))

        elif mtype == "spectate_ok":
            self.spectating = True

        elif mtype == "error":
            self.last_error = msg.get("message")

    def receive_messages(self): #keep listening to server in background
        buffer = ""

        while self.running: #keep listening while teh client is active
            try:
                try:
                    data = self.sock.recv(4096).decode()
                except socket.timeout:
                    continue
                if not data: #nothing comes back,connection was closed
                    self.running = False
                    break

                buffer += data

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)

                    if line.strip() == "":
                        continue

                    msg = json.loads(line) #convert JOSN test into python dictionary
                    self.handle_message(msg)

            except Exception as e: #stores the error and stops the client
                self.last_error = str(e)
                self.running = False
                break

    def start_receiver_thread(self): #starts receive_messages() in a background thread.
        thread = threading.Thread(target=self.receive_messages, daemon=True)
        thread.start()

    def close(self): #close client socket
        self.running = False
        if self.sock:
            self.sock.close()


def main():
    # temporary terminal testing
    client = GameClient()

    host = input("Enter server IP: ")
    port = int(input("Enter port: "))
    username = input("Enter username: ")

    client.connect(host, port)
    client.join(username)
    client.start_receiver_thread()

    print("Connected. Type commands:")
    print("challenge <username>")
    print("accept <username>")
    print("move <UP/DOWN/LEFT/RIGHT>")
    print("chat <message>")
    print("spectate")
    print("state")
    print("players")
    print("quit")

    while client.running:
        command = input("> ").strip()

        if command == "quit":
            client.close()
            break

        elif command.startswith("challenge "):
            target = command[len("challenge "):].strip()
            client.challenge(target)

        elif command.startswith("accept "):
            target = command[len("accept "):].strip()
            client.accept(target)

        elif command.startswith("move "):
            direction = command[len("move "):].strip()
            client.move(direction)

        elif command.startswith("chat "):
            text = command[len("chat "):].strip()
            client.send_chat(text)

        elif command == "spectate":
            client.spectate()

        elif command == "state":
            print("Game state:", client.game_state)

        elif command == "players":
            print("Players:", client.player_list)

        else:
            print("Unknown command")

        # small status display for testing
        if client.last_challenge_from:
            print("Last challenge from:", client.last_challenge_from)

        if client.last_error:
            print("Error:", client.last_error)
            client.last_error = None

        if client.game_over:
            print("Winner:", client.winner)
            print("Final health:", client.final_health)


if __name__ == "__main__":
    main()
