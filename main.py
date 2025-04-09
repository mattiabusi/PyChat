import dearpygui.dearpygui as dpg
import socket
import threading
import json
import time
from datetime import datetime

# Configurazione del client
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5555
BUFFER_SIZE = 4096


class ChatClient:
    def __init__(self):
        self.username = ""
        self.connected = False
        self.socket = None
        self.messages = []
        self.users_online = []
        self.receive_thread = None
        self.setup_gui()

    def setup_gui(self):
        dpg.create_context()
        dpg.create_viewport(title="Chat App", width=600, height=500)

        # Tema personalizzato
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (70, 70, 80), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (50, 50, 60), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Button, (100, 100, 120), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (120, 120, 140), category=dpg.mvThemeCat_Core)

        dpg.bind_theme(global_theme)

        # Finestra di login
        with dpg.window(label="Login", width=300, height=200, pos=(150, 150), tag="login_window"):
            dpg.add_text("Inserisci il tuo nome utente:")
            dpg.add_input_text(tag="username_input", callback=self.on_username_input)
            dpg.add_text("Server IP (default: 127.0.0.1):")
            dpg.add_input_text(tag="server_ip_input", default_value=SERVER_HOST)
            dpg.add_text("Server Porta (default: 5555):")
            dpg.add_input_text(tag="server_port_input", default_value=str(SERVER_PORT))
            dpg.add_button(label="Connetti", callback=self.connect_to_server)
            dpg.add_text("", tag="login_status", color=(255, 100, 100))

        # Finestra principale della chat (inizialmente nascosta)
        with dpg.window(label="Chat", width=600, height=500, show=False, tag="chat_window"):
            # Layout a due colonne
            with dpg.group(horizontal=True):
                # Area messaggi (colonna sinistra)
                with dpg.child_window(width=450, height=400, tag="messages_panel"):
                    dpg.add_text("Connessione al server in corso...", tag="welcome_text")

                # Lista utenti (colonna destra)
                with dpg.child_window(width=130, height=400, tag="users_panel"):
                    dpg.add_text("Utenti Online:", tag="users_online_header")
                    dpg.add_separator()
                    dpg.add_text("", tag="users_list")

            # Area input messaggio
            with dpg.group(horizontal=True):
                dpg.add_input_text(tag="message_input", width=450, on_enter=True, callback=self.send_message)
                dpg.add_button(label="Invia", callback=self.send_message)

            # Pulsante disconnetti
            dpg.add_button(label="Disconnetti", callback=self.disconnect)

        dpg.setup_dearpygui()
        dpg.show_viewport()

    def on_username_input(self, sender, app_data):
        self.username = app_data

    def update_messages_display(self):
        dpg.delete_item("messages_panel", children_only=True)

        for msg in self.messages:
            if msg["type"] == "message":
                timestamp = msg.get("timestamp", "")
                formatted_time = ""
                if timestamp:
                    try:
                        dt = datetime.fromtimestamp(timestamp)
                        formatted_time = dt.strftime("[%H:%M:%S] ")
                    except:
                        formatted_time = ""

                sender = msg.get("sender", "Anonimo")
                content = msg.get("content", "")

                if sender == self.username:
                    # Stile per i messaggi dell'utente corrente
                    dpg.add_text(f"{formatted_time}Tu: {content}", color=(200, 230, 200))
                else:
                    # Stile per i messaggi degli altri utenti
                    dpg.add_text(f"{formatted_time}{sender}: {content}")
            elif msg["type"] == "system":
                # Stile per i messaggi di sistema
                dpg.add_text(msg["content"], color=(180, 180, 220))

    def update_users_list(self):
        if not self.users_online:
            user_list_text = "Nessun utente online"
        else:
            user_list_text = "\n".join(self.users_online)
        dpg.set_value("users_list", user_list_text)

    def connect_to_server(self):
        if not self.username:
            dpg.set_value("login_status", "Inserisci un nome utente valido!")
            return

        # Ottieni l'indirizzo e la porta del server dai campi di input
        server_host = dpg.get_value("server_ip_input") or SERVER_HOST
        try:
            server_port = int(dpg.get_value("server_port_input") or SERVER_PORT)
        except ValueError:
            dpg.set_value("login_status", "Porta non valida! Usa un numero intero.")
            return

        try:
            # Crea una socket TCP/IP
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((server_host, server_port))

            # Invia le informazioni di login
            login_message = {
                "type": "login",
                "username": self.username,
                "timestamp": time.time()
            }
            self.socket.send(json.dumps(login_message).encode('utf-8'))

            # Mostra la finestra di chat e nascondi il login
            dpg.hide_item("login_window")
            dpg.show_item("chat_window")
            dpg.set_primary_window("chat_window", True)

            # Imposta lo stato come connesso
            self.connected = True

            # Avvia thread di ricezione messaggi
            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()

        except Exception as e:
            error_msg = f"Errore di connessione: {str(e)}"
            dpg.set_value("login_status", error_msg)

    def send_message(self):
        if not self.connected or not self.socket:
            return

        message_content = dpg.get_value("message_input")
        if not message_content.strip():
            return

        # Crea oggetto messaggio
        message = {
            "type": "message",
            "content": message_content,
            "timestamp": time.time()
        }

        try:
            # Invia il messaggio al server
            self.socket.send(json.dumps(message).encode('utf-8'))

            # Pulisci il campo di input
            dpg.set_value("message_input", "")
        except Exception as e:
            system_msg = {
                "type": "system",
                "content": f"Errore nell'invio del messaggio: {str(e)}",
                "timestamp": time.time()
            }
            self.messages.append(system_msg)
            self.update_messages_display()

            # Disconnetti in caso di errore
            self.disconnect(reconnect=False)

    def receive_messages(self):
        """Riceve messaggi dal server"""
        while self.connected and self.socket:
            try:
                # Ricevi dati dal server
                data = self.socket.recv(BUFFER_SIZE)
                if not data:
                    # Se non ci sono dati, il server potrebbe essere disconnesso
                    break

                # Decodifica e processa il messaggio
                message = json.loads(data.decode('utf-8'))
                message_type = message.get("type", "")

                if message_type == "message" or message_type == "system":
                    # Aggiungi il messaggio alla lista e aggiorna il display
                    self.messages.append(message)

                    # Aggiorna l'interfaccia nel thread principale
                    dpg.split_frame()  # Necessario per aggiornare l'interfaccia da un thread secondario
                    self.update_messages_display()

                elif message_type == "users_list":
                    # Aggiorna la lista degli utenti
                    self.users_online = message.get("users", [])

                    # Aggiorna l'interfaccia nel thread principale
                    dpg.split_frame()
                    self.update_users_list()

                elif message_type == "error":
                    # Gestisci messaggi di errore dal server
                    error_content = message.get("content", "Errore sconosciuto")

                    # Torna alla schermata di login
                    self.disconnect(reconnect=False)
                    dpg.split_frame()
                    dpg.set_value("login_status", error_content)

            except json.JSONDecodeError:
                print("Errore nel decodificare il messaggio JSON")
                continue
            except Exception as e:
                print(f"Errore nella ricezione dei messaggi: {e}")
                # In caso di errore, disconnetti il client
                self.disconnect(reconnect=False)
                break

    def disconnect(self, reconnect=True):
        """Disconnette il client dal server"""
        if self.connected and self.socket:
            try:
                # Invia messaggio di disconnessione al server
                disconnect_msg = {
                    "type": "disconnect",
                    "timestamp": time.time()
                }
                self.socket.send(json.dumps(disconnect_msg).encode('utf-8'))
            except:
                pass

            # Chiudi la socket
            try:
                self.socket.close()
            except:
                pass

            # Aggiorna lo stato
            self.connected = False
            self.socket = None

        # Reset dei dati
        self.messages = []
        self.users_online = []

        if reconnect:
            # Torna alla schermata di login
            dpg.hide_item("chat_window")
            dpg.show_item("login_window")
            dpg.set_primary_window("login_window", True)
            dpg.set_value("login_status", "")

    def run(self):
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()

        # Disconnetti quando l'app viene chiusa
        self.disconnect(reconnect=False)
        dpg.destroy_context()


if __name__ == "__main__":
    client = ChatClient()
    client.run()
