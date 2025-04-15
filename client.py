import socket
import threading

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345


def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(1024).decode()
            if not msg:
                break
            print(msg)
        except:
            break


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_HOST, SERVER_PORT))

    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    try:
        while True:
            msg = input()
            client.sendall(msg.encode())
    except KeyboardInterrupt:
        print("Disconnessione...")
        client.close()


if __name__ == "__main__":
    main()
