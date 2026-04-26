import socket
import json #convert python dictionaries into JSON text
import threading
# terminal based client

def send_message(sock, data):
    msg = json.dumps(data) + "\n"
    sock.sendall(msg.encode()) #turn string into bytes adn send whole message thru socket

def handle_message(msg): #after you receive message from server
    mtype = msg.get("type")

    if mtype == "username_ok":
        print("Username accepted")

    elif mtype == "username_taken":
        print("Username already taken")

    elif mtype == "player_list":
        print("Players online:", msg["players"])

    elif mtype == "challenged":
        print("You were challenged by", msg["by"])

    elif mtype == "game_start":
        print("Game started! You are player", msg["player_id"])

    elif mtype == "game_state":
        print("Game update")
        print("Health:", msg["health"])
        print("Time left:", msg["time_left"])

    elif mtype == "game_over":
        print("Game over")
        print("Winner:", msg["winner"])
        print("Final health:", msg["health"])

    elif mtype == "chat":
        print(f"{msg['from']}: {msg['message']}")

    elif mtype == "spectate_ok":
        print("Spectate mode enabled")

    elif mtype == "error":
        print("Error:", msg["message"])

    else:
        print("Unknown message:", msg)

def receive_messages(sock): #keeps listening to server forever
    buffer = ""

    while True: #keep listening until connecyion closes
        try:
            data = sock.recv(4096).decode() #reads up to 4096 bytes from socket and turns them to text
            if not data: #no data recieved
                print("Disconnected from server.")
                break #server probably closed connection

            buffer += data

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip() == "":
                    continue

                msg = json.loads(line)
                handle_message(msg)

        except:
            print("Connection closed.")
            break

def command_loop(sock): #to type commands in termianl
    while True:
        command = input("> ").strip()

        if command.lower() == "quit":
            print("Closing client...") #close socket and stop
            sock.close()
            break

        elif command.startswith("challenge "):
            target = command[len("challenge "):].strip()
            send_message(sock, {
                "type": "challenge",
                "target": target
            })

        elif command.startswith("accept "):
            target = command[len("accept "):].strip()
            send_message(sock, {
                "type": "accept",
                "target": target
            })

        elif command.startswith("move "):
            direction = command[len("move "):].strip().upper()
            send_message(sock, {
                "type": "input",
                "direction": direction
            })

        elif command.startswith("chat "):
            text = command[len("chat "):].strip()
            send_message(sock, {
                "type": "chat",
                "message": text
            })

        elif command == "spectate":
            send_message(sock, {
                "type": "spectate"
            })

        else:
            print("Commands:")
            print("  challenge <username>")
            print("  accept <username>")
            print("  move <UP/DOWN/LEFT/RIGHT>")
            print("  chat <message>")
            print("  spectate")
            print("  quit")

def main():
    host = input("Enter server IP: ")
    port = int(input("Enter port: "))
    username = input("Enter username: ")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    join_msg = {
        "type": "join",
        "username": username
    }
    send_message(sock, join_msg)

    receiver_thread = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    receiver_thread.start()

    print("Type commands after joining.")
    command_loop(sock)

if __name__ == "__main__":
    main()
