import socket
import threading
import datetime
import sys
import time
from dearpygui import dearpygui as dpg

# Configurazione del client
SERVER_HOST = '172.20.10.2'  # Indirizzo del server (localhost)
SERVER_PORT = 12345  # Porta del server
client = None  # Socket del client
nickname = ""  # Nickname del giocatore
connected = False  # Stato della connessione


# Mostra messaggi nella chat
def log_to_output(msg):
    # Aggiungi timestamp
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    dpg.add_text(f"[{timestamp}] {msg}", parent="ChatScroll")

    # Auto-scroll in basso
    scroll_amount = dpg.get_item_height("ChatScroll")
    dpg.set_y_scroll("ChatScroll", scroll_amount)


# Ricezione messaggi dal server
def receive_messages():
    global connected
    while connected:
        try:
            msg = client.recv(1024).decode()
            if not msg:
                break

            # Gestisce i dati della classifica
            if msg.startswith("[SCORE_DATA]"):
                update_score_table(msg)
            else:
                log_to_output(msg)
        except Exception as e:
            if connected:  # Evita messaggi di errore se la disconnessione è intenzionale
                log_to_output(f"❌ Errore di connessione: {str(e)}")
            break

    # Se usciamo dal loop e siamo ancora connessi, significa che la connessione è caduta
    if connected:
        connected = False
        log_to_output("❌ Connessione al server persa.")
        dpg.configure_item("ReconnectButton", show=True)


def update_score_table(msg):
    """Aggiorna la tabella dei punteggi con i dati ricevuti dal server"""
    # Cancella le righe attuali
    try:
        dpg.delete_item("ScoreTable", children_only=True)
    except:
        pass

    # Estrai i dati dal messaggio
    data = msg.replace("[SCORE_DATA]", "").strip()
    if not data:
        return

    lines = data.split("\n")

    # Ordina i punteggi in ordine decrescente
    score_data = []
    for line in lines:
        if ":" in line:
            name, score = line.strip().split(":")
            score_data.append((name, int(score)))

    score_data.sort(key=lambda x: x[1], reverse=True)

    # Aggiorna la tabella con i dati ricevuti
    for name, score in score_data:
        with dpg.table_row(parent="ScoreTable"):
            dpg.add_text(name)
            dpg.add_text(str(score))


# Invia messaggi o comandi
def send_callback():
    global nickname, connected

    if not connected:
        log_to_output("❌ Non sei connesso al server.")
        return

    message = dpg.get_value("Input").strip()
    if not message:
        return

    # Gestione dei comandi client-side
    if message.startswith("/"):
        if message == "/clear" or message == "/pulisci":
            dpg.delete_item("ChatScroll", children_only=True)
            log_to_output("🧹 Chat pulita.")
        elif message == "/whoami":
            log_to_output(f"👤 Il tuo nickname è: {nickname}")
        elif message == "/time" or message == "/ora":
            log_to_output(f"🕒 Orario attuale: {datetime.datetime.now().strftime('%H:%M:%S')}")
        elif message == "/exit" or message == "/esci":
            exit_game()
        # Inoltra tutti gli altri comandi al server
        else:
            try:
                client.sendall(message.encode())
            except:
                log_to_output("❌ Errore durante l'invio del comando.")
    else:
        # Invia un messaggio normale o un tentativo di indovinare
        try:
            client.sendall(message.encode())
        except:
            log_to_output("❌ Errore durante l'invio.")

    dpg.set_value("Input", "")


# Connessione al server
def connect_to_server():
    global client, nickname, connected

    # Ottieni il nickname dall'input
    nickname = dpg.get_value("Nickname").strip()

    if not nickname:
        log_to_output("❌ Inserisci un nickname valido.")
        return

    if len(nickname) < 3:
        log_to_output("❌ Il nickname deve avere almeno 3 caratteri.")
        return

    log_to_output(f"🔄 Tentativo di connessione al server {SERVER_HOST}:{SERVER_PORT}...")

    try:
        # Crea un nuovo socket per il client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_HOST, SERVER_PORT))
        connected = True
        log_to_output("✅ Connessione al server riuscita!")
    except Exception as e:
        log_to_output(f"❌ Connessione fallita: {str(e)}")
        return

    # Avvia thread per ricevere messaggi
    threading.Thread(target=receive_messages, daemon=True).start()

    # Passa alla finestra di gioco
    dpg.hide_item("LoginWindow")
    dpg.show_item("GameWindow")
    dpg.configure_item("ReconnectButton", show=False)

    # Mostra messaggio di benvenuto nella chat
    log_to_output(f"🎉 Benvenuto nel gioco, {nickname}! Indovina un numero tra 1 e 100.")


def exit_game():
    """Gestisce l'uscita dal gioco"""
    global connected

    try:
        if connected and client:
            client.sendall("/exit".encode())
            connected = False
            client.close()
    except:
        pass

    log_to_output("👋 Uscita dal gioco.")
    time.sleep(1)  # Breve pausa per mostrare il messaggio
    dpg.stop_dearpygui()
    sys.exit()


def reconnect():
    """Tenta di riconnettersi al server usando lo stesso nickname"""
    global connected

    if connected:
        return

    connect_to_server()


# Main entry point
def main():
    # Inizializza DearPyGUI
    dpg.create_context()

    # Crea tema
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, [32, 32, 32, 255])
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, [25, 90, 140, 255])
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, [40, 110, 170, 255])
            dpg.add_theme_color(dpg.mvThemeCol_Button, [50, 120, 190, 255])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [70, 140, 210, 255])
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)

    dpg.bind_theme(global_theme)

    # Finestra di login
    with dpg.window(label="Login - Indovina il Numero", tag="LoginWindow", width=350, height=200, no_close=True):
        dpg.add_text("Benvenuto nel gioco 'Indovina il Numero'!")
        dpg.add_text("Inserisci un nickname per connetterti.")
        dpg.add_separator()
        dpg.add_spacer(height=10)
        dpg.add_input_text(label="Nickname", tag="Nickname", hint="Inserisci almeno 3 caratteri")
        dpg.add_spacer(height=10)
        with dpg.group(horizontal=True):
            dpg.add_button(label="Connetti", callback=connect_to_server, width=150)
            dpg.add_button(label="Esci", callback=exit_game, width=150)

    # Finestra principale di gioco
    with dpg.window(label="Indovina il Numero", tag="GameWindow", width=800, height=600, show=False, no_close=True):
        with dpg.group(horizontal=True):
            # Area chat a sinistra
            with dpg.child_window(tag="ChatScroll", width=550, height=450):
                dpg.add_text("Benvenuto nel gioco 'Indovina il Numero'!")
                dpg.add_text("Connettiti al server per iniziare.")

            # Classifica a destra
            with dpg.child_window(width=230, height=450):
                dpg.add_text("🏆 Classifica:", bullet=True)
                with dpg.table(tag="ScoreTable", header_row=True, resizable=True,
                               borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True,
                               width=220):
                    dpg.add_table_column(label="Giocatore")
                    dpg.add_table_column(label="Punti")

        # Area input
        with dpg.group(horizontal=True):
            dpg.add_input_text(tag="Input", width=640, on_enter=True, callback=send_callback,
                               hint="Messaggio / Numero / Comando")
            dpg.add_button(label="Invia", callback=send_callback, width=70)
            dpg.add_button(label="Esci", callback=exit_game, width=70)

        # Bottone di riconnessione (inizialmente nascosto)
        dpg.add_button(label="Riconnetti", callback=reconnect, tag="ReconnectButton", width=100, show=False)

        # Area informazioni
        with dpg.collapsing_header(label="Comandi e istruzioni", default_open=True):
            dpg.add_text("🎯 Come giocare:")
            dpg.add_text("1. Indovina un numero tra 1 e 100")
            dpg.add_text("2. Il server ti dirà se il tuo tentativo è troppo alto o troppo basso")
            dpg.add_text("3. Chi indovina per primo guadagna un punto!")
            dpg.add_separator()
            dpg.add_text("📋 Comandi disponibili sul server:")
            dpg.add_text("/help - Mostra tutti i comandi disponibili")
            dpg.add_text("/score o /classifica - Mostra la classifica")
            dpg.add_text("/online - Mostra giocatori connessi")
            dpg.add_text("/numero - Ricorda il range di numeri")
            dpg.add_separator()
            dpg.add_text("🖥 Comandi client:")
            dpg.add_text("/clear o /pulisci - Pulisce la chat")
            dpg.add_text("/whoami - Mostra il tuo nickname")
            dpg.add_text("/time o /ora - Mostra l'ora attuale")
            dpg.add_text("/exit o /esci - Esce dal gioco")

    # Configura finestra primaria
    dpg.set_primary_window("LoginWindow", True)
    dpg.create_viewport(title="Indovina il Numero", width=820, height=650)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()