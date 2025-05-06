import socket
import threading
import datetime
import sys
import time
from dearpygui import dearpygui as dpg

SERVER_HOST = '192.168.1.50'
SERVER_PORT = 12345
client = None
nickname = ""
connected = False

def log_to_output(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    dpg.add_text(f"[{timestamp}] {msg}", parent="ChatScroll")
    scroll_amount = dpg.get_item_height("ChatScroll")
    dpg.set_y_scroll("ChatScroll", scroll_amount)

def update_score_table(msg):
    try:
        dpg.delete_item("ScoreTable", children_only=True)
    except:
        pass
    data = msg.replace("[SCORE_DATA]", "").strip()
    if not data:
        return
    score_data = []
    for line in data.split("\n"):
        if ":" in line:
            name, points = line.strip().split(":")
            score_data.append((name, int(points)))
    score_data.sort(key=lambda x: x[1], reverse=True)
    for name, points in score_data:
        with dpg.table_row(parent="ScoreTable"):
            dpg.add_text(name)
            dpg.add_text(str(points))

def receive_messages():
    global connected
    while connected:
        try:
            msg = client.recv(1024).decode()
            if not msg:
                break
            if msg.startswith("[SCORE_DATA]"):
                update_score_table(msg)
            else:
                log_to_output(msg)
        except Exception as e:
            if connected:
                log_to_output(f"❌ Errore di connessione: {str(e)}")
            break
    if connected:
        connected = False
        log_to_output("❌ Connessione al server persa.")
        dpg.configure_item("ReconnectButton", show=True)

def send_callback():
    global nickname, connected
    if not connected:
        log_to_output("❌ Non sei connesso al server.")
        return
    message = dpg.get_value("Input").strip()
    if not message:
        return
    if message.startswith("/"):
        if message == "/clear" or message == "/pulisci":
            dpg.delete_item("ChatScroll", children_only=True)
            log_to_output("🧹 Chat pulita.")
        elif message == "/nome":
            log_to_output(f"👤 Il tuo nickname è: {nickname}")
        elif message == "/time" or message == "/ora":
            log_to_output(f"🕒 Orario attuale: {datetime.datetime.now().strftime('%H:%M:%S')}")
        elif message == "/exit" or message == "/esci":
            exit_game()
        else:
            try:
                client.sendall(message.encode())
            except:
                log_to_output("❌ Errore durante l'invio del comando.")
    else:
        try:
            client.sendall(message.encode())
        except:
            log_to_output("❌ Errore durante l'invio.")
    dpg.set_value("Input", "")

def connect_to_server():
    global client, nickname, connected
    nickname = dpg.get_value("Nickname").strip()
    if not nickname:
        log_to_output("❌ Inserisci un nickname valido.")
        return
    if len(nickname) < 3:
        log_to_output("❌ Il nickname deve avere almeno 3 caratteri.")
        return
    log_to_output(f"🔄 Tentativo di connessione al server {SERVER_HOST}:{SERVER_PORT}...")
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_HOST, SERVER_PORT))
        client.recv(1024)
        client.sendall(nickname.encode())
        connected = True
        log_to_output("✅ Connessione al server riuscita!")
    except Exception as e:
        log_to_output(f"❌ Connessione fallita: {str(e)}")
        return
    threading.Thread(target=receive_messages, daemon=True).start()
    dpg.hide_item("LoginWindow")
    dpg.show_item("GameWindow")
    dpg.configure_item("ReconnectButton", show=False)
    log_to_output(f"🎉 Benvenuto nel gioco, {nickname}! Indovina la parola segreta.")

def exit_game():
    global connected
    try:
        if connected and client:
            client.sendall("/exit".encode())
            connected = False
            client.close()
    except:
        pass
    log_to_output("👋 Uscita dal gioco.")
    time.sleep(1)
    dpg.stop_dearpygui()
    sys.exit()

def reconnect():
    global connected
    if connected:
        return
    connect_to_server()

def main():
    dpg.create_context()
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
    with dpg.window(label="Login - Indovina la Parola", tag="LoginWindow", width=350, height=200, no_close=True):
        dpg.add_text("Benvenuto nel gioco 'Indovina la Parola'!")
        dpg.add_text("Inserisci un nickname per connetterti.")
        dpg.add_separator()
        dpg.add_spacer(height=10)
        dpg.add_input_text(label="Nickname", tag="Nickname", hint="Inserisci almeno 3 caratteri")
        dpg.add_spacer(height=10)
        with dpg.group(horizontal=True):
            dpg.add_button(label="Connetti", callback=connect_to_server, width=150)
            dpg.add_button(label="Esci", callback=exit_game, width=150)
    with dpg.window(label="Indovina la Parola", tag="GameWindow", width=800, height=600, show=False, no_close=True):
        with dpg.group(horizontal=True):
            with dpg.child_window(tag="ChatScroll", width=550, height=450):
                dpg.add_text("Benvenuto nel gioco 'Indovina la Parola'!")
                dpg.add_text("Connettiti al server per iniziare.")
            with dpg.child_window(width=230, height=450):
                dpg.add_text("🏆 Classifica:", bullet=True)
                with dpg.table(tag="ScoreTable", header_row=True, resizable=True,
                               borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True,
                               width=220, height=400):
                    dpg.add_table_column(label="Giocatore", width_fixed=True, init_width_or_weight=120)
                    dpg.add_table_column(label="Punti", width_fixed=True, init_width_or_weight=80)
                dpg.add_spacer(height=10)
                dpg.add_button(label="Aggiorna Classifica",
                               callback=lambda: client.sendall("/score".encode()) if connected else None, width=220)
        with dpg.group(horizontal=True):
            dpg.add_input_text(tag="Input", width=640, on_enter=True, callback=send_callback,
                               hint="Messaggio / Lettera / Parola / Comando")
            dpg.add_button(label="Invia", callback=send_callback, width=70)
            dpg.add_button(label="Esci", callback=exit_game, width=70)
        dpg.add_button(label="Riconnetti", callback=reconnect, tag="ReconnectButton", width=100, show=False)
        with dpg.collapsing_header(label="Comandi e istruzioni", default_open=True):
            dpg.add_text("🎯 Come giocare:")
            dpg.add_text("1. Indovina la parola segreta proposta dal server")
            dpg.add_text("2. Puoi provare a indovinare singole lettere o l'intera parola")
            dpg.add_text("3. Chi indovina per primo la parola guadagna un punto!")
            dpg.add_separator()
            dpg.add_text("📋 Comandi disponibili sul server:")
            dpg.add_text("/help - Mostra tutti i comandi disponibili")
            dpg.add_text("/score o /classifica - Mostra la classifica")
            dpg.add_text("/online - Mostra giocatori connessi")
            dpg.add_text("/hint - Richiedi un suggerimento")
            dpg.add_separator()
            dpg.add_text("🖥 Comandi client:")
            dpg.add_text("/clear o /pulisci - Pulisce la chat")
            dpg.add_text("/nome - Mostra il tuo nickname")
            dpg.add_text("/time o /ora - Mostra l'ora attuale")
            dpg.add_text("/exit o /esci - Esce dal gioco")
    dpg.set_primary_window("LoginWindow", True)
    dpg.create_viewport(title="Indovina la Parola", width=820, height=650)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
