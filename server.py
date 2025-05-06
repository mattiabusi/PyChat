# Importazione delle librerie necessarie
import socket  # Per la comunicazione di rete
import threading  # Per gestire più connessioni contemporaneamente
import random  # Per la scelta casuale delle parole
import time  # Per gestire i tempi di attesa

# Configurazione del server
HOST = '192.168.1.50'  # Indirizzo IP del server
PORT = 12345  # Porta di ascolto del server
clients = {}  # Dizionario che tiene traccia delle connessioni: {connessione: nickname}
scores = {}  # Dizionario dei punteggi: {nickname: punteggio}
word_list = ["python", "programmazione", "computer", "algoritmo", "sviluppatore", "intelligenza"]  # Lista di parole da indovinare
current_word = random.choice(word_list)  # Parola corrente da indovinare
guessed_letters = set()  # Insieme delle lettere già indovinate
game_over = False  # Stato del gioco (True quando qualcuno ha indovinato)
lock = threading.Lock()  # Semaforo per la sincronizzazione tra thread
SCORES_FILE = "scores.txt"  # File per salvare i punteggi

def broadcast(message, exclude_conn=None):
    """
    Invia un messaggio a tutti i client connessi
    Args:
        message (str): Messaggio da inviare
        exclude_conn (socket): Client da escludere (opzionale)
    """
    for conn in clients:
        if conn != exclude_conn:  # Invia a tutti tranne quello escluso
            try:
                conn.sendall(message.encode())  # Invia il messaggio codificato
            except:
                pass  # Ignora errori di invio

def send_score_update():
    """
    Invia a tutti i client la classifica aggiornata
    """
    # Ordina i punteggi in modo decrescente
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Formatta i dati della classifica
    score_data = "[SCORE_DATA]"  # Marcatore per identificare i dati della classifica
    for name, points in sorted_scores:
        score_data += f"{name}:{points}\n"  # Aggiunge ogni punteggio

    # Invia a tutti i client connessi
    for conn in clients:
        try:
            conn.sendall(score_data.encode())
        except:
            pass  # Ignora errori di invio

def get_word_progress():
    """
    Genera la rappresentazione della parola con le lettere indovinate
    Returns:
        str: Parola con lettere indovinate e trattini per quelle mancanti
    """
    progress = []
    for letter in current_word:
        if letter in guessed_letters:
            progress.append(letter)  # Mostra lettere indovinate
        else:
            progress.append("_")  # Trattino per lettere non indovinate
    return " ".join(progress)  # Unisce con spazi

def handle_client(conn, addr):
    """
    Gestisce la comunicazione con un singolo client
    Args:
        conn (socket): Oggetto connessione del client
        addr (tuple): Indirizzo del client (IP, porta)
    """
    global game_over, current_word, guessed_letters
    try:
        # Richiede e verifica il nickname
        conn.sendall("🎮 Benvenuto! Inserisci il tuo nickname: ".encode())
        nickname = conn.recv(1024).decode().strip()

        # Controlla nickname duplicati
        while nickname in [name for name in clients.values()]:
            conn.sendall("❌ Nickname già in uso. Inserisci un nuovo nickname: ".encode())
            nickname = conn.recv(1024).decode().strip()

        # Aggiunge il client alla lista
        clients[conn] = nickname

        # Inizializza il punteggio per nuovi giocatori
        if nickname not in scores:
            scores[nickname] = 0
            save_scores()

        # Comunica l'ingresso del giocatore
        welcome = f"👋 {nickname} si è unito al gioco!"
        print(welcome)
        broadcast(f"{welcome}\n")

        # Invia istruzioni e stato iniziale
        conn.sendall(f"🎯 Indovina la parola segreta! ({len(current_word)} lettere)\n".encode())
        conn.sendall(f"Parola: {get_word_progress()}\n".encode())

        # Aggiorna la classifica
        send_score_update()

        # Loop principale di gestione messaggi
        while True:
            msg = conn.recv(1024).decode().strip().lower()

            # Gestione comandi
            if msg.startswith("/"):
                handle_command(msg, conn, nickname)
                continue

            # Se il gioco è in pausa tra una partita e l'altra
            if game_over:
                conn.sendall("⏳ Attendi che inizi una nuova partita...\n".encode())
                continue

            # Gestione tentativi (lettera singola o parola intera)
            if len(msg) == 1 and msg.isalpha():
                handle_letter_guess(msg, conn, nickname)
            elif len(msg) > 1 and msg.isalpha():
                handle_word_guess(msg, conn, nickname)
            else:
                broadcast(f"💬 {nickname}: {msg}\n", exclude_conn=None)

    except Exception as e:
        print(f"[ERRORE] {e}")
    finally:
        # Pulizia in caso di disconnessione
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
    """
    Gestisce un tentativo di indovinare una lettera
    Args:
        letter (str): Lettera proposta
        conn (socket): Connessione del client
        nickname (str): Nickname del giocatore
    """
    global game_over, guessed_letters

    with lock:  # Sincronizzazione tra thread
        if letter in guessed_letters:
            conn.sendall(f"ℹ️ La lettera '{letter}' è già stata provata!\n".encode())
            return

        guessed_letters.add(letter)  # Aggiunge la lettera a quelle provate

        if letter in current_word:
            # Lettera corretta
            conn.sendall(f"✅ Bravo! La lettera '{letter}' è presente nella parola!\n".encode())
            broadcast(f"✨ {nickname} ha indovinato la lettera '{letter}'!\n", exclude_conn=conn)

            # Mostra lo stato aggiornato
            word_progress = get_word_progress()
            broadcast(f"Parola: {word_progress}\n")

            # Verifica se la parola è stata completamente indovinata
            if "_" not in word_progress:
                handle_word_guess(current_word, conn, nickname)
        else:
            # Lettera errata
            conn.sendall(f"❌ La lettera '{letter}' non è presente nella parola.\n".encode())
            broadcast(f"💢 {nickname} ha provato la lettera '{letter}' (non presente)\n", exclude_conn=conn)

def handle_word_guess(word, conn, nickname):
    """
    Gestisce un tentativo di indovinare la parola intera
    Args:
        word (str): Parola proposta
        conn (socket): Connessione del client
        nickname (str): Nickname del giocatore
    """
    global game_over, scores

    with lock:  # Sincronizzazione tra thread
        if word == current_word:
            # Parola indovinata correttamente
            game_over = True
            scores[nickname] = scores.get(nickname, 0) + 1  # Incrementa punteggio
            save_scores()

            # Comunica la vittoria
            victory_message = f"\n🎉 {nickname} ha indovinato la parola '{current_word}'! Guadagna 1 punto! 🎉\n"
            broadcast(victory_message)
            print(f"[VINCITORE] {nickname} ha indovinato '{current_word}'")

            # Aggiorna la classifica
            send_score_update()

            # Riavvia il gioco dopo 5 secondi
            threading.Timer(5.0, restart_game).start()
        else:
            # Parola errata
            conn.sendall("❌ Non è la parola corretta. Prova ancora!\n".encode())
            broadcast(f"💢 {nickname} ha provato la parola '{word}' (errata)\n", exclude_conn=conn)

def handle_command(msg, conn, nickname):
    """
    Gestisce i comandi speciali inviati dai client
    Args:
        msg (str): Comando ricevuto
        conn (socket): Connessione del client
        nickname (str): Nickname del giocatore
    """
    if msg == "/score" or msg == "/classifica":
        # Mostra la classifica testuale
        score_list = "\n".join(
            [f"{name}: {points}" for name, points in sorted(scores.items(), key=lambda x: x[1], reverse=True)])
        conn.sendall(f"\n🏆 Classifica:\n{score_list}\n".encode())

        # Invia anche i dati formattati per la tabella
        send_score_update()

    elif msg == "/help":
        # Mostra l'aiuto con i comandi disponibili
        help_text = "\n📋 Comandi disponibili:\n"
        help_text += "/help - mostra questo messaggio di aiuto\n"
        help_text += "/score o /classifica - mostra la classifica dei giocatori\n"
        help_text += "/hint - mostra un suggerimento (una lettera casuale non ancora indovinata)\n"
        help_text += "/online - mostra i giocatori connessi\n"
        help_text += "\nPer giocare: scrivi una lettera o prova a indovinare la parola intera\n"
        help_text += "Per chattare: scrivi un messaggio qualsiasi (non una lettera o parola)\n"

        conn.sendall(help_text.encode())

    elif msg == "/hint":
        # Fornisce un suggerimento (lettera non ancora indovinata)
        remaining_letters = [letter for letter in current_word if letter not in guessed_letters]
        if remaining_letters:
            hint = random.choice(remaining_letters)
            conn.sendall(f"💡 Suggerimento: prova la lettera '{hint}'\n".encode())
        else:
            conn.sendall("ℹ️ Tutte le lettere sono già state indovinate!\n".encode())

    elif msg == "/online":
        # Mostra la lista dei giocatori connessi
        online_list = ", ".join(clients.values())
        conn.sendall(f"👥 Giocatori online: {online_list}\n".encode())

    elif msg.startswith("/kick ") and nickname in ["admin", "moderatore"]:
        # Comando admin per espellere un giocatore
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
        # Comando non riconosciuto
        conn.sendall("❓ Comando sconosciuto. Scrivi /help per assistenza.\n".encode())

def restart_game():
    """
    Prepara una nuova partita con una nuova parola
    """
    global current_word, guessed_letters, game_over
    with lock:  # Sincronizzazione tra thread
        current_word = random.choice(word_list)  # Sceglie nuova parola
        guessed_letters = set()  # Resetta le lettere indovinate
        game_over = False  # Ripristina lo stato del gioco
        broadcast(f"\n🔄 Nuova partita iniziata! Indovina la parola ({len(current_word)} lettere)\n")
        broadcast(f"Parola: {get_word_progress()}\n")
        print(f"[NUOVA PARTITA] Parola segreta: {current_word}")

def load_scores():
    """
    Carica i punteggi dal file di salvataggio
    """
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
    """
    Salva i punteggi nel file di salvataggio
    """
    try:
        with open(SCORES_FILE, "w") as f:
            for name, points in scores.items():
                f.write(f"{name}:{points}\n")
    except Exception as e:
        print(f"[ERRORE] Impossibile salvare i punteggi: {e}")

def main():
    """
    Funzione principale del server
    """
    # Carica i punteggi esistenti
    load_scores()

    # Configura il socket del server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # Avvia il server
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[SERVER AVVIATO] Ascolto su {HOST}:{PORT}")
        print(f"[INFO] Parola iniziale da indovinare: {current_word}")

        # Accetta connessioni in loop
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
        # Pulizia alla chiusura del server
        for conn in clients.copy():
            try:
                conn.close()
            except:
                pass

        server.close()
        print("[SERVER] Arrestato.")
        save_scores()  # Salva i punteggi prima di chiudere

if __name__ == "__main__":
    main()
