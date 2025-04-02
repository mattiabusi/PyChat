import socket

server_address = ('127.0.0.1', 65535)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect(server_address)

    while True:
        message = input("Inserisci un messaggio (o 'exit' per uscire): ")
        if message.lower() == 'exit':
            break

        client_socket.sendall(message.encode())
        data = client_socket.recv(4096)
        print(f"Risposta dal server: {data.decode()}")
