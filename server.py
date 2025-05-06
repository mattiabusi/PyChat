import socket
import threading
import random
import time

INDIRIZZO_SERVER = '192.168.1.50'
PORTA = 12345
client_connessi = {}  # {conn: nickname}
punteggi = {}  # {nickname: punteggio}
lista_parole = ["python", "programmazione", "computer", "algoritmo", "sviluppatore", "intelligenza"]
parola_corrente = random.choice(lista_parole)
lettere_indovinate = set()
gioco_terminato = False
blocco = threading.Lock()
FILE_PUNTEGGI = "scores.txt"

def trasmette(messaggio, escludi_client=None):
    for conn in client_connessi:
        if conn != escludi_client:
            try:
                conn.sendall(messaggio.encode())
            except:
                pass

def aggiorna_classifica():
    punteggi_ordinati = sorted(punteggi.items(), key=lambda x: x[1], reverse=True)
    dati_classifica = "[DATI_CLASSIFICA]"
    for nome, punti in punteggi_ordinati:
        dati_classifica += f"{nome}:{punti}\n"
    for conn in client_connessi:
        try:
            conn.sendall(dati_classifica.encode())
        except:
            pass

def stato_parola():
    progresso = []
    for lettera in parola_corrente:
        if lettera in lettere_indovinate:
            progresso.append(lettera)
        else:
            progresso.append("_")
    return " ".join(progresso)

def gestisci_client(conn, addr):
    global gioco_terminato, parola_corrente, lettere_indovinate
    try:
        conn.sendall("🎮 Benvenuto! Inserisci il tuo nickname: ".encode())
        nickname = conn.recv(1024).decode().strip()

        while nickname in [nome for nome in client_connessi.values()]:
            conn.sendall("❌ Nickname già in uso. Inserisci un nuovo nickname: ".encode())
            nickname = conn.recv(1024).decode().strip()

        client_connessi[conn] = nickname

        if nickname not in punteggi:
            punteggi[nickname] = 0
            salva_punteggi()

        benvenuto = f"👋 {nickname} si è unito al gioco!"
        print(benvenuto)
        trasmette(f"{benvenuto}\n")

        conn.sendall(f"🎯 Indovina la parola segreta! ({len(parola_corrente)} lettere)\n".encode())
        conn.sendall(f"Parola: {stato_parola()}\n".encode())

        aggiorna_classifica()

        while True:
            messaggio = conn.recv(1024).decode().strip().lower()

            if messaggio.startswith("/"):
                gestisci_comando(messaggio, conn, nickname)
                continue

            if gioco_terminato:
                conn.sendall("⏳ Attendi che inizi una nuova partita...\n".encode())
                continue

            if len(messaggio) == 1 and messaggio.isalpha():
                gestisci_lettera(messaggio, conn, nickname)
            elif len(messaggio) > 1 and messaggio.isalpha():
                gestisci_parola(messaggio, conn, nickname)
            else:
                trasmette(f"💬 {nickname}: {messaggio}\n", exclude_conn=None)

    except Exception as e:
        print(f"[ERRORE] {e}")
    finally:
        if conn in client_connessi:
            nickname = client_connessi[conn]
            print(f"[DISCONNESSO] {nickname}")
            trasmette(f"👋 {nickname} si è disconnesso.\n")
            client_connessi.pop(conn, None)

        try:
            conn.close()
        except:
            pass

def gestisci_lettera(lettera, conn, nickname):
    global gioco_terminato, lettere_indovinate

    with blocco:
        if lettera in lettere_indovinate:
            conn.sendall(f"ℹ️ La lettera '{lettera}' è già stata provata!\n".encode())
            return

        lettere_indovinate.add(lettera)

        if lettera in parola_corrente:
            conn.sendall(f"✅ Bravo! La lettera '{lettera}' è presente nella parola!\n".encode())
            trasmette(f"✨ {nickname} ha indovinato la lettera '{lettera}'!\n", exclude_conn=conn)
            progresso = stato_parola()
            trasmette(f"Parola: {progresso}\n")
            if "_" not in progresso:
                gestisci_parola(parola_corrente, conn, nickname)
        else:
            conn.sendall(f"❌ La lettera '{lettera}' non è presente nella parola.\n".encode())
            trasmette(f"💢 {nickname} ha provato la lettera '{lettera}' (non presente)\n", exclude_conn=conn)

def gestisci_parola(parola, conn, nickname):
    global gioco_terminato, punteggi

    with blocco:
        if parola == parola_corrente:
            gioco_terminato = True
            punteggi[nickname] = punteggi.get(nickname, 0) + 1
            salva_punteggi()
            messaggio_vittoria = f"\n🎉 {nickname} ha indovinato la parola '{parola_corrente}'! Guadagna 1 punto! 🎉\n"
            trasmette(messaggio_vittoria)
            print(f"[VINCITORE] {nickname} ha indovinato '{parola_corrente}'")
            aggiorna_classifica()
            threading.Timer(5.0, riavvia_gioco).start()
        else:
            conn.sendall("❌ Non è la parola corretta. Prova ancora!\n".encode())
            trasmette(f"💢 {nickname} ha provato la parola '{parola}' (errata)\n", exclude_conn=conn)

def gestisci_comando(messaggio, conn, nickname):
    if messaggio == "/score" or messaggio == "/classifica":
        lista_punteggi = "\n".join([f"{nome}: {punti}" for nome, punti in sorted(punteggi.items(), key=lambda x: x[1], reverse=True)])
        conn.sendall(f"\n🏆 Classifica:\n{lista_punteggi}\n".encode())
        aggiorna_classifica()
    elif messaggio == "/help":
        testo_aiuto = "\n📋 Comandi disponibili:\n"
        testo_aiuto += "/help - mostra questo messaggio di aiuto\n"
        testo_aiuto += "/score o /classifica - mostra la classifica dei giocatori\n"
        testo_aiuto += "/hint - mostra un suggerimento (una lettera casuale non ancora indovinata)\n"
        testo_aiuto += "/online - mostra i giocatori connessi\n"
        testo_aiuto += "\nPer giocare: scrivi una lettera o prova a indovinare la parola intera\n"
        testo_aiuto += "Per chattare: scrivi un messaggio qualsiasi (non una lettera o parola)\n"
        conn.sendall(testo_aiuto.encode())
    elif messaggio == "/hint":
        lettere_rimanenti = [lettera for lettera in parola_corrente if lettera not in lettere_indovinate]
        if lettere_rimanenti:
            suggerimento = random.choice(lettere_rimanenti)
            conn.sendall(f"💡 Suggerimento: prova la lettera '{suggerimento}'\n".encode())
        else:
            conn.sendall("ℹ️ Tutte le lettere sono già state indovinate!\n".encode())
    elif messaggio == "/online":
        lista_online = ", ".join(client_connessi.values())
        conn.sendall(f"👥 Giocatori online: {lista_online}\n".encode())
    elif messaggio.startswith("/kick ") and nickname in ["admin", "moderatore"]:
        target = messaggio.split(" ", 1)[1].strip()
        for c, nick in client_connessi.items():
            if nick == target:
                trasmette(f"👢 {target} è stato espulso dal gioco.\n")
                try:
                    c.sendall("👢 Sei stato espulso dal gioco.\n".encode())
                    c.close()
                except:
                    pass
                client_connessi.pop(c, None)
                return
        conn.sendall(f"❌ Giocatore {target} non trovato.\n".encode())
    else:
        conn.sendall("❓ Comando sconosciuto. Scrivi /help per assistenza.\n".encode())

def riavvia_gioco():
    global parola_corrente, lettere_indovinate, gioco_terminato
    with blocco:
        parola_corrente = random.choice(lista_parole)
        lettere_indovinate = set()
        gioco_terminato = False
        trasmette(f"\n🔄 Nuova partita iniziata! Indovina la parola ({len(parola_corrente)} lettere)\n")
        trasmette(f"Parola: {stato_parola()}\n")
        print(f"[NUOVA PARTITA] Parola segreta: {parola_corrente}")

def carica_punteggi():
    try:
        with open(FILE_PUNTEGGI, "r") as f:
            for linea in f:
                if ":" in linea:
                    nome, punti = linea.strip().split(":")
                    punteggi[nome] = int(punti)
        print(f"[INFO] Punteggi caricati da {FILE_PUNTEGGI}")
    except FileNotFoundError:
        print(f"[INFO] File {FILE_PUNTEGGI} non trovato, verrà creato")
    except Exception as e:
        print(f"[ERRORE] Impossibile caricare i punteggi: {e}")

def salva_punteggi():
    try:
        with open(FILE_PUNTEGGI, "w") as f:
            for nome, punti in punteggi.items():
                f.write(f"{nome}:{punti}\n")
    except Exception as e:
        print(f"[ERRORE] Impossibile salvare i punteggi: {e}")

def main():
    carica_punteggi()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((INDIRIZZO_SERVER, PORTA))
        server.listen(5)
        print(f"[SERVER AVVIATO] Ascolto su {INDIRIZZO_SERVER}:{PORTA}")
        print(f"[INFO] Parola iniziale da indovinare: {parola_corrente}")
        while True:
            conn, addr = server.accept()
            print(f"[NUOVA CONNESSIONE] {addr}")
            threading.Thread(target=gestisci_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[SERVER] Arresto in corso...")
    except Exception as e:
        print(f"[ERRORE FATALE] {e}")
    finally:
        for conn in client_connessi.copy():
            try:
                conn.close()
            except:
                pass
        server.close()
        print("[SERVER] Arrestato.")
        salva_punteggi()

if __name__ == "__main__":
    main()
