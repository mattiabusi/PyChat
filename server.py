import socket
import threading
import random
import time

HOST = '0.0.0.0'  # Ascolta su tutte le interfacce
PORT = 12345
clients = {}  # {conn: nickname}
scores = {}  # {nickname: punteggio}
game_number = random.randint(1, 100)
game_over = False
lock = threading.Lock()
SCORES_FILE = "scores.txt"


def broadcast(message, exclude_conn=None):
    """Invia un messaggio a tutti i client, opzionalmente escludendo un client specifico"""
    for conn in clients:
        if conn != exclude_conn:
            try:
                conn.sendall(message.encode())
            except:
                pass


def send_score_update():
    """Invia un aggiornamento della classifica a tutti i client"""
    score_data = "[SCORE_DATA]"
    for name, points in scores.items():
        score_data += f"{name}:{points}\n"

    for conn in clients:
        try:
            conn.sendall(score_data.encode())
        except:
            pass


def handle_client(conn, addr):
    """Gestisce la connessione con un client"""
    global game_over, game_number
    try:
        conn.sendall("🎮 Benvenuto! Inserisci il tuo nickname: ".encode())
        nickname = conn.recv(1024).decode().strip()

        # Controlla se il nickname è già in uso
        while nickname in [name for name in clients.values()]:
            conn.sendall("❌ Nickname già in uso. Inserisci un nuovo nickname: ".encode())
            nickname = conn.recv(1024).decode().strip()

        clients[conn] = nickname

        # Inizializza il punteggio se il giocatore è nuovo
        if nickname not in scores:
            scores[nickname] = 0
            save_scores()

        welcome = f"👋 {nickname} si è unito al gioco!"
        print(welcome)
        broadcast(f"{welcome}\n")

        # Invia messaggio di benvenuto e istruzioni
        conn.sendall("🎯 Indovina un numero tra 1 e 100 oppure scrivi /help\n".encode())

        # Invia aggiornamento della classifica
        send_score_update()

        # Loop principale per gestire i messaggi del client
        while True:
            msg = conn.recv(1024).decode().strip()

            # Gestione dei comandi
            if msg.startswith("/"):
                handle_command(msg, conn, nickname)
                continue

            # Verifica se il gioco è in pausa
            if game_over:
                conn.sendall("⏳ Attendi che inizi una nuova partita...\n".encode())
                continue

            # Se non è un numero, trattalo come un messaggio di chat
            if not msg.isdigit():
                broadcast(f"💬 {nickname}: {msg}\n", exclude_conn=None)
                continue

            # Gestione dei tentativi di indovinare
            guess = int(msg)
            if guess < 1 or guess > 100:
                conn.sendall("❌ Il numero deve essere compreso tra 1 e 100!\n".encode())
                continue

            with lock:
                if guess < game_number:
                    conn.sendall("📉 Troppo basso! Prova con un numero più grande.\n".encode())
                elif guess > game_number:
                    conn.sendall("📈 Troppo alto! Prova con un numero più piccolo.\n".encode())
                else:
                    game_over = True
                    scores[nickname] = scores.get(nickname, 0) + 1
                    save_scores()

                    # Annuncia il vincitore
                    victory_message = f"\n🎉 {nickname} ha indovinato il numero {game_number}! Guadagna 1 punto! 🎉\n"
                    broadcast(victory_message)
                    print(f"[VINCITORE] {nickname} ha indovinato {game_number}")

                    # Invia aggiornamento della classifica
                    send_score_update()

                    # Riavvia il gioco dopo 5 secondi
                    threading.Timer(5.0, restart_game).start()

    except Exception as e:
        print(f"[ERRORE] {e}")
    finally:
        if conn in clients:
            nickname = clients[conn]
            print(f"[DISCONNESSO] {nickname}")
            broadcast(f"👋 {nickname} si è disconnesso.\n")
            clients.pop(conn, None)

        try:
            conn.close()
        except:
            pass


def handle_command(msg, conn, nickname):
    """Gestisce i comandi inviati dal client"""
    if msg == "/score" or msg == "/classifica":
        score_list = "\n".join(
            [f"{name}: {points}" for name, points in sorted(scores.items(), key=lambda x: x[1], reverse=True)])
        conn.sendall(f"\n🏆 Classifica:\n{score_list}\n".encode())

        # Invia anche i dati formattati per la visualizzazione tabellare
        send_score_update()

    elif msg == "/help":
        help_text = "\n📋 Comandi disponibili:\n"
        help_text += "/help - mostra questo messaggio di aiuto\n"
        help_text += "/score o /classifica - mostra la classifica dei giocatori\n"
        help_text += "/numero - mostra il range di numeri (1-100)\n"
        help_text += "/online - mostra i giocatori connessi\n"
        help_text += "\nPer giocare: scrivi semplicemente un numero tra 1 e 100\n"
        help_text += "Per chattare: scrivi un messaggio qualsiasi (non un numero)\n"

        conn.sendall(help_text.encode())

    elif msg == "/numero":
        conn.sendall("🎮 Devi indovinare un numero tra 1 e 100.\n".encode())

    elif msg == "/online":
        online_list = ", ".join(clients.values())
        conn.sendall(f"👥 Giocatori online: {online_list}\n".encode())

    elif msg.startswith("/kick ") and nickname in ["admin", "moderatore"]:  # Admin only
        target = msg.split(" ", 1)[1].strip()
        for c, nick in clients.items():
            if nick == target:
                broadcast(f"👢 {target} è stato espulso dal gioco.\n")
                try:
                    c.sendall("👢 Sei stato espulso dal gioco.\n".encode())
                    c.close()
                except:
                    pass
                clients.pop(c, None)
                return
        conn.sendall(f"❌ Giocatore {target} non trovato.\n".encode())

    else:
        conn.sendall("❓ Comando sconosciuto. Scrivi /help per assistenza.\n".encode())


def restart_game():
    """Riavvia il gioco con un nuovo numero"""
    global game_number, game_over
    with lock:
        game_number = random.randint(1, 100)
        game_over = False
        broadcast("\n🔄 Nuova partita iniziata! Indovina un numero tra 1 e 100\n")
        print(f"[NUOVA PARTITA] Numero segreto: {game_number}")


def load_scores():
    """Carica i punteggi da file"""
    try:
        with open(SCORES_FILE, "r") as f:
            for line in f:
                if ":" in line:
                    name, points = line.strip().split(":")
                    scores[name] = int(points)
        print(f"[INFO] Punteggi caricati da {SCORES_FILE}")
    except FileNotFoundError:
        print(f"[INFO] File {SCORES_FILE} non trovato, verrà creato")
    except Exception as e:
        print(f"[ERRORE] Impossibile caricare i punteggi: {e}")


def save_scores():
    """Salva i punteggi su file"""
    try:
        with open(SCORES_FILE, "w") as f:
            for name, points in scores.items():
                f.write(f"{name}:{points}\n")
    except Exception as e:
        print(f"[ERRORE] Impossibile salvare i punteggi: {e}")


def main():
    """Funzione principale del server"""
    # Carica i punteggi salvati
    load_scores()

    # Crea il socket del server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[SERVER AVVIATO] Ascolto su {HOST}:{PORT}")
        print(f"[INFO] Numero iniziale da indovinare: {game_number}")

        # Loop principale per accettare connessioni
        while True:
            conn, addr = server.accept()
            print(f"[NUOVA CONNESSIONE] {addr}")

            # Avvia un thread per gestire il client
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

    except KeyboardInterrupt:
        print("\n[SERVER] Arresto in corso...")
    except Exception as e:
        print(f"[ERRORE FATALE] {e}")
    finally:
        # Chiudi tutte le connessioni
        for conn in clients.copy():
            try:
                conn.close()
            except:
                pass

        # Chiudi il server
        server.close()
        print("[SERVER] Arrestato.")
        save_scores()


if __name__ == "__main__":
    main()