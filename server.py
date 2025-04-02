import socket

# Server TCP
server_address = ('127.0.0.1', 65535)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(server_address)
server_socket.listen(5)  # Numero massimo di connessioni in attesa

print(f"Server TCP in ascolto su {server_address[0]}:{server_address[1]}")

while True:
    print("In attesa di una connessione...")
    connection, client_address = server_socket.accept()
    try:
        print(f"Connessione da: {client_address}")
        while True:
            data = connection.recv(4096)
            if data:
                print(f"Ricevuto dal client: {data.decode()}")
                response = data.upper()
                connection.sendall(response)
                print(f"Inviato al client: {response.decode()}")
            else:
                print(f"Nessun altro dato da {client_address}")
                break
    finally:
        connection.close()