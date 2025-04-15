import socket
import threading
import random

HOST = '0.0.0.0'
PORT = 12345

clients = {}  # {conn: nickname}
scores = {}   # {nickname: vittorie}
game_number = random.randint(1, 100)
game_over = False
lock = threading.Lock()

def broadcast(message, exclude_conn=None):
    for conn in clients:
        if conn != exclude_conn:
            try:
                conn.sendall(message.encode())
            except:
                pass

def handle_client(conn, addr):
    global game_over, game_number

    try:
        conn.sendall("🎮 Benvenuto! Inserisci il tuo nickname: ".encode())
        nickname = conn.recv(1024).decode().strip()
        clients[conn] = nickname
        welcome = f"👋 {nickname} si è unito al gioco!"
        print(welcome)
        broadcast(f"{welcome}\n")

        conn.sendall("🎯 Indovina un numero tra 1 e 100 oppure scrivi /help\n".encode())

        while True:
            msg = conn.recv(1024).decode().strip()

            if msg.startswith("/"):
                handle_command(msg, conn, nickname)
                continue

            if game_over:
                conn.sendall("⏳ Attendi che inizi una nuova partita...\n".encode())
                continue

            if not msg.isdigit():
                broadcast(f" {nickname}: {msg}\n", exclude_conn=None)
                continue

            guess = int(msg)

            with lock:
                if guess < game_number:
                    conn.sendall(" Troppo basso!\n".encode())
                elif guess > game_number:
                    conn.sendall(" Troppo alto!\n".encode())
                else:
                    game_over = True
                    scores[nickname] = scores.get(nickname, 0) + 1
                    broadcast(f"\n {nickname} ha indovinato il numero {game_number}!\n")
                    threading.Timer(5.0, restart_game).start()
    except:
        pass
    finally:
        print(f"[DISCONNESSO] {clients.get(conn)}")
        broadcast(f" {clients.get(conn)} si è disconnesso.\n")
        clients.pop(conn, None)
        conn.close()

def handle_command(msg, conn, nickname):
    if msg == "/score":
        score_list = "\n".join(f"{name}: {points}" for name, points in scores.items())
        conn.sendall(f"\n Classifica:\n{score_list}\n".encode())
    elif msg == "/help":
        help_text = "\n Comandi disponibili:\n/help - mostra aiuto\n/score - classifica\nScrivi un numero o un messaggio per chattare.\n"
        conn.sendall(help_text.encode())
    else:
        conn.sendall("Comando sconosciuto. Scrivi /help per assistenza.\n".encode())

def restart_game():
    global game_number, game_over
    game_number = random.randint(1, 100)
    game_over = False
    broadcast("\n Nuova partita iniziata! Indovina un numero tra 1 e 100\n")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER AVVIATO] Ascolto su {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
