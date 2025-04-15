import socket
import threading
import random

HOST = '0.0.0.0'
PORT = 12345

clients = []
game_number = random.randint(1, 100)
game_over = False
lock = threading.Lock()

def broadcast(message):
    for client in clients:
        try:
            client.sendall(message.encode())
        except:
            clients.remove(client)

def handle_client(conn, addr):
    global game_number, game_over

    print(f"[NUOVO GIOCATORE] {addr}")
    conn.sendall("🎮 Benvenuto! Indovina un numero tra 1 e 100\n".encode())

    while True:
        try:
            guess = conn.recv(1024).decode().strip()
            if not guess:
                break

            with lock:
                if game_over:
                    conn.sendall("⏳ Attendi che inizi una nuova partita...\n".encode())
                    continue

                if not guess.isdigit():
                    conn.sendall("❌ Inserisci un numero valido!\n".encode())
                    continue

                guess = int(guess)
                if guess < game_number:
                    conn.sendall("📉 Troppo basso!\n".encode())
                elif guess > game_number:
                    conn.sendall("📈 Troppo alto!\n".encode())
                else:
                    winner_msg = f"🏆 {addr} ha indovinato il numero {game_number}!\n"
                    broadcast(winner_msg)
                    print(winner_msg)
                    game_over = True

                    # Avvia nuova partita dopo 5 secondi
                    threading.Timer(5.0, restart_game).start()

        except:
            break

    print(f"[DISCONNESSO] {addr}")
    clients.remove(conn)
    conn.close()

def restart_game():
    global game_number, game_over
    game_number = random.randint(1, 100)
    game_over = False
    broadcast("\n🔁 Nuova partita iniziata! Indovina un numero tra 1 e 100\n")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER ATTIVO] In ascolto su {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        clients.append(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    main()
