import socket
import threading
import random
import time

HOST = '192.168.1.50'
PORT = 12345
clients = {}
scores = {}
word_list = ["python", "programmazione", "computer", "algoritmo", "sviluppatore", "intelligenza"]
current_word = random.choice(word_list)
guessed_letters = set()
game_over = False
lock = threading.Lock()
SCORES_FILE = "scores.txt"

def broadcast(message, exclude_conn=None):
    for conn in clients:
        if conn != exclude_conn:
            try:
                conn.sendall(message.encode())
            except:
                pass

def send_score_update():
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    score_data = "[SCORE_DATA]"
    for name, points in sorted_scores:
        score_data += f"{name}:{points}\n"
    for conn in clients:
        try:
            conn.sendall(score_data.encode())
        except:
            pass

def get_word_progress():
    progress = []
    for letter in current_word:
        if letter in guessed_letters:
            progress.append(letter)
        else:
            progress.append("_")
    return " ".join(progress)

def handle_client(conn, addr):
    global game_over, current_word, guessed_letters
    try:
        conn.sendall("🎮 Benvenuto! Inserisci il tuo nickname: ".encode())
        nickname = conn.recv(1024).decode().strip()
        while nickname in [name for name in clients.values()]:
            conn.sendall("❌ Nickname già in uso. Inserisci un nuovo nickname: ".encode())
            nickname = conn.recv(1024).decode().strip()
        clients[conn] = nickname
        if nickname not in scores:
            scores[nickname] = 0
            save_scores()
        welcome = f"👋 {nickname} si è unito al gioco!"
        print(welcome)
        broadcast(f"{welcome}\n")
        conn.sendall(f"🎯 Indovina la parola segreta! ({len(current_word)} lettere)\n".encode())
        conn.sendall(f"Parola: {get_word_progress()}\n".encode())
        send_score_update()
        while True:
            msg = conn.recv(1024).decode().strip().lower()
            if msg.startswith("/"):
                handle_command(msg, conn, nickname)
                continue
            if game_over:
                conn.sendall("⏳ Attendi che inizi una nuova partita...\n".encode())
                continue
            if len(msg) == 1 and msg.isalpha():
                handle_letter_guess(msg, conn, nickname)
            elif len(msg) > 1 and msg.isalpha():
                handle_word_guess(msg, conn, nickname)
            else:
                broadcast(f"💬 {nickname}: {msg}\n", exclude_conn=None)
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

def handle_letter_guess(letter, conn, nickname):
    global game_over, guessed_letters
    with lock:
        if letter in guessed_letters:
            conn.sendall(f"ℹ️ La lettera '{letter}' è già stata provata!\n".encode())
            return
        guessed_letters.add(letter)
        if letter in current_word:
            conn.sendall(f"✅ Bravo! La lettera '{letter}' è presente nella parola!\n".encode())
            broadcast(f"✨ {nickname} ha indovinato la lettera '{letter}'!\n", exclude_conn=conn)
            word_progress = get_word_progress()
            broadcast(f"Parola: {word_progress}\n")
            if "_" not in word_progress:
                handle_word_guess(current_word, conn, nickname)
        else:
            conn.sendall(f"❌ La lettera '{letter}' non è presente nella parola.\n".encode())
            broadcast(f"💢 {nickname} ha provato la lettera '{letter}' (non presente)\n", exclude_conn=conn)

def handle_word_guess(word, conn, nickname):
    global game_over, scores
    with lock:
        if word == current_word:
            game_over = True
            scores[nickname] = scores.get(nickname, 0) + 1
            save_scores()
            victory_message = f"\n🎉 {nickname} ha indovinato la parola '{current_word}'! Guadagna 1 punto! 🎉\n"
            broadcast(victory_message)
            print(f"[VINCITORE] {nickname} ha indovinato '{current_word}'")
            send_score_update()
            threading.Timer(5.0, restart_game).start()
        else:
            conn.sendall("❌ Non è la parola corretta. Prova ancora!\n".encode())
            broadcast(f"💢 {nickname} ha provato la parola '{word}' (errata)\n", exclude_conn=conn)

def handle_command(msg, conn, nickname):
    if msg == "/score" or msg == "/classifica":
        score_list = "\n".join([f"{name}: {points}" for name, points in sorted(scores.items(), key=lambda x: x[1], reverse=True)])
        conn.sendall(f"\n🏆 Classifica:\n{score_list}\n".encode())
        send_score_update()
    elif msg == "/help":
        help_text = "\n📋 Comandi disponibili:\n"
        help_text += "/help - mostra questo messaggio di aiuto\n"
        help_text += "/score o /classifica - mostra la classifica dei giocatori\n"
        help_text += "/hint - mostra un suggerimento (una lettera casuale non ancora indovinata)\n"
        help_text += "/online - mostra i giocatori connessi\n"
        help_text += "\nPer giocare: scrivi una lettera o prova a indovinare la parola intera\n"
        help_text += "Per chattare: scrivi un messaggio qualsiasi (non una lettera o parola)\n"
        conn.sendall(help_text.encode())
    elif msg == "/hint":
        remaining_letters = [letter for letter in current_word if letter not in guessed_letters]
        if remaining_letters:
            hint = random.choice(remaining_letters)
            conn.sendall(f"💡 Suggerimento: prova la lettera '{hint}'\n".encode())
        else:
            conn.sendall("ℹ️ Tutte le lettere sono già state indovinate!\n".encode())
    elif msg == "/online":
        online_list = ", ".join(clients.values())
        conn.sendall(f"👥 Giocatori online: {online_list}\n".encode())
    elif msg.startswith("/kick ") and nickname in ["admin", "moderatore"]:
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
    global current_word, guessed_letters, game_over
    with lock:
        current_word = random.choice(word_list)
        guessed_letters = set()
        game_over = False
        broadcast(f"\n🔄 Nuova partita iniziata! Indovina la parola ({len(current_word)} lettere)\n")
        broadcast(f"Parola: {get_word_progress()}\n")
        print(f"[NUOVA PARTITA] Parola segreta: {current_word}")

def load_scores():
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
    try:
        with open(SCORES_FILE, "w") as f:
            for name, points in scores.items():
                f.write(f"{name}:{points}\n")
    except Exception as e:
        print(f"[ERRORE] Impossibile salvare i punteggi: {e}")

def main():
    load_scores()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[SERVER AVVIATO] Ascolto su {HOST}:{PORT}")
        print(f"[INFO] Parola iniziale da indovinare: {current_word}")
        while True:
            conn, addr = server.accept()
            print(f"[NUOVA CONNESSIONE] {addr}")
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[SERVER] Arresto in corso...")
    except Exception as e:
        print(f"[ERRORE FATALE] {e}")
    finally:
        for conn in clients.copy():
            try:
                conn.close()
            except:
                pass
        server.close()
        print("[SERVER] Arrestato.")
        save_scores()

if __name__ == "__main__":
    main()
