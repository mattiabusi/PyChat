import socket
import threading
import datetime
import sys
import time
from dearpygui import dearpygui as dpg

INDIRIZZO_SERVER = '192.168.1.50'
PORTA_SERVER = 12345
client = None
soprannome = ""
connesso = False

def registra_messaggio(messaggio):
    orario = datetime.datetime.now().strftime("%H:%M:%S")
    dpg.add_text(f"[{orario}] {messaggio}", parent="ScorrimentoChat")
    altezza_scorrimento = dpg.get_item_height("ScorrimentoChat")
    dpg.set_y_scroll("ScorrimentoChat", altezza_scorrimento)

def aggiorna_classifica(messaggio):
    try:
        dpg.delete_item("TabellaClassifica", children_only=True)
    except:
        pass
    dati = messaggio.replace("[DATI_CLASSIFICA]", "").strip()
    if not dati:
        return
    punteggi = []
    for riga in dati.split("\n"):
        if ":" in riga:
            nome, punti = riga.strip().split(":")
            punteggi.append((nome, int(punti)))
    punteggi.sort(key=lambda x: x[1], reverse=True)
    for nome, punti in punteggi:
        with dpg.table_row(parent="TabellaClassifica"):
            dpg.add_text(nome)
            dpg.add_text(str(punti))

def ricevi_messaggi():
    global connesso
    while connesso:
        try:
            messaggio = client.recv(1024).decode()
            if not messaggio:
                break
            if messaggio.startswith("[DATI_CLASSIFICA]"):
                aggiorna_classifica(messaggio)
            else:
                registra_messaggio(messaggio)
        except Exception as e:
            if connesso:
                registra_messaggio(f"❌ Errore di connessione: {str(e)}")
            break
    if connesso:
        connesso = False
        registra_messaggio("❌ Connessione al server persa.")
        dpg.configure_item("PulsanteRiconnessione", show=True)

def invia_messaggio():
    global soprannome, connesso
    if not connesso:
        registra_messaggio("❌ Non sei connesso al server.")
        return
    messaggio = dpg.get_value("InputTesto").strip()
    if not messaggio:
        return
    if messaggio.startswith("/"):
        if messaggio == "/clear" or messaggio == "/pulisci":
            dpg.delete_item("ScorrimentoChat", children_only=True)
            registra_messaggio("🧹 Chat pulita.")
        elif messaggio == "/nome":
            registra_messaggio(f"👤 Il tuo soprannome è: {soprannome}")
        elif messaggio == "/time" or messaggio == "/ora":
            registra_messaggio(f"🕒 Orario attuale: {datetime.datetime.now().strftime('%H:%M:%S')}")
        elif messaggio == "/exit" or messaggio == "/esci":
            termina_gioco()
        else:
            try:
                client.sendall(messaggio.encode())
            except:
                registra_messaggio("❌ Errore durante l'invio del comando.")
    else:
        try:
            client.sendall(messaggio.encode())
        except:
            registra_messaggio("❌ Errore durante l'invio.")
    dpg.set_value("InputTesto", "")

def connetti_al_server():
    global client, soprannome, connesso
    soprannome = dpg.get_value("InputSoprannome").strip()
    if not soprannome:
        registra_messaggio("❌ Inserisci un soprannome valido.")
        return
    if len(soprannome) < 3:
        registra_messaggio("❌ Il soprannome deve avere almeno 3 caratteri.")
        return
    registra_messaggio(f"🔄 Tentativo di connessione al server {INDIRIZZO_SERVER}:{PORTA_SERVER}...")
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((INDIRIZZO_SERVER, PORTA_SERVER))
        client.recv(1024)
        client.sendall(soprannome.encode())
        connesso = True
        registra_messaggio("✅ Connessione al server riuscita!")
    except Exception as e:
        registra_messaggio(f"❌ Connessione fallita: {str(e)}")
        return
    threading.Thread(target=ricevi_messaggi, daemon=True).start()
    dpg.hide_item("FinestraLogin")
    dpg.show_item("FinestraGioco")
    dpg.configure_item("PulsanteRiconnessione", show=False)
    registra_messaggio(f"🎉 Benvenuto nel gioco, {soprannome}! Indovina la parola segreta.")

def termina_gioco():
    global connesso
    try:
        if connesso and client:
            client.sendall("/exit".encode())
            connesso = False
            client.close()
    except:
        pass
    registra_messaggio("👋 Uscita dal gioco.")
    time.sleep(1)
    dpg.stop_dearpygui()
    sys.exit()

def riconnetti():
    global connesso
    if connesso:
        return
    connetti_al_server()

def main():
    dpg.create_context()
    with dpg.theme() as tema_globale:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, [32, 32, 32, 255])
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, [25, 90, 140, 255])
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, [40, 110, 170, 255])
            dpg.add_theme_color(dpg.mvThemeCol_Button, [50, 120, 190, 255])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [70, 140, 210, 255])
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)
    dpg.bind_theme(tema_globale)
    
    with dpg.window(label="Login - Indovina la Parola", tag="FinestraLogin", width=350, height=200, no_close=True):
        dpg.add_text("Benvenuto nel gioco 'Indovina la Parola'!")
        dpg.add_text("Inserisci un soprannome per connetterti.")
        dpg.add_separator()
        dpg.add_spacer(height=10)
        dpg.add_input_text(label="Soprannome", tag="InputSoprannome", hint="Inserisci almeno 3 caratteri")
        dpg.add_spacer(height=10)
        with dpg.group(horizontal=True):
            dpg.add_button(label="Connetti", callback=connetti_al_server, width=150)
            dpg.add_button(label="Esci", callback=termina_gioco, width=150)
    
    with dpg.window(label="Indovina la Parola", tag="FinestraGioco", width=800, height=600, show=False, no_close=True):
        with dpg.group(horizontal=True):
            with dpg.child_window(tag="ScorrimentoChat", width=550, height=450):
                dpg.add_text("Benvenuto nel gioco 'Indovina la Parola'!")
                dpg.add_text("Connettiti al server per iniziare.")
            with dpg.child_window(width=230, height=450):
                dpg.add_text("🏆 Classifica:", bullet=True)
                with dpg.table(tag="TabellaClassifica", header_row=True, resizable=True,
                             borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True,
                             width=220, height=400):
                    dpg.add_table_column(label="Giocatore", width_fixed=True, init_width_or_weight=120)
                    dpg.add_table_column(label="Punti", width_fixed=True, init_width_or_weight=80)
                dpg.add_spacer(height=10)
                dpg.add_button(label="Aggiorna Classifica",
                             callback=lambda: client.sendall("/score".encode()) if connesso else None, width=220)
        
        with dpg.group(horizontal=True):
            dpg.add_input_text(tag="InputTesto", width=640, on_enter=True, callback=invia_messaggio,
                             hint="Messaggio / Lettera / Parola / Comando")
            dpg.add_button(label="Invia", callback=invia_messaggio, width=70)
            dpg.add_button(label="Esci", callback=termina_gioco, width=70)
        
        dpg.add_button(label="Riconnetti", callback=riconnetti, tag="PulsanteRiconnessione", width=100, show=False)
        
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
            dpg.add_text("/nome - Mostra il tuo soprannome")
            dpg.add_text("/time o /ora - Mostra l'ora attuale")
            dpg.add_text("/exit o /esci - Esce dal gioco")
    
    dpg.set_primary_window("FinestraLogin", True)
    dpg.create_viewport(title="Indovina la Parola", width=820, height=650)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
