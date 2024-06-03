import socket
import threading
import os
import sqlite3

clients = {}
active_sessions = {}


def handle_client(client_socket, client_address):
    global active_sessions
    print(f"[NEW CONNECTION] {client_address} connected.")

    while True:
        data = client_socket.recv(1024).decode('utf-8')

        if not data:
            break

        mode = data.split(' ')[0]
        print(f"[{client_address}] {data}")

        if data.startswith("login"):
            _, username, password = data.split()

            if authenticate_user(username, password):
                clients[username] = client_socket
                client_socket.sendall("Login successful!".encode('utf-8'))
                send_connected_clients()

            else:
                client_socket.sendall(
                    "Invalid username or password.".encode('utf-8'))

        elif data.startswith("create_user"):
            _, username, password = data.split()

            if create_user(username, password):
                client_socket.sendall(
                    "User created successfully!".encode('utf-8'))

            else:
                client_socket.sendall(
                    "Failed to create user. Please try again.".encode('utf-8'))

        elif data.startswith("request_clients"):
            # Send list of currently connected clients
            client_socket.sendall(",".join(clients.keys()).encode('utf-8'))

        elif data.startswith("connect"):
            _, sender_username, recipient_username = data.split()
            establish_connection(sender_username, recipient_username)

        elif data.startswith("file"):
            if len(data) > 4:
                file_info = data[5:]
                broadcast_file(username, recipient_username, file_info)

        elif mode == "msg":
            if len(data) > 3:
                message = data[4:]
                broadcast_message(username, recipient_username, message)

        elif data == "disconnect":
            print(
                f"[{username}] Client requested to disconnect. Closing connection.")

            if active_sessions:
                for key, _ in list(active_sessions.items()):
                    if username in key:
                        del active_sessions[key]

        elif data == "quit":
            print(
                f"[{username}] Client requested to quit. Closing connection.")
            client_socket.close()
            if username in clients:
                del clients[username]

            if active_sessions:
                for key, _ in list(active_sessions.items()):
                    if username in key:
                        del active_sessions[key]
            break

    print(f"[DISCONNECTED] {client_address} disconnected.")
    client_socket.close()


def broadcast_message(sender_username, recipient_username, message):

    for (sender, recipient), client_socket in active_sessions.items():
        if sender == recipient_username:
            try:
                client_socket.sendall(
                    f"[{sender_username}]: {message}".encode('utf-8'))
            except Exception as e:
                print(
                    f"Error broadcasting message to {recipient_username}: {e}")


def send_connected_clients():
    connected_clients_str = "CONNECTED_CLIENTS:" + ",".join(clients.keys())

    for client_socket in clients.values():
        try:
            client_socket.sendall(connected_clients_str.encode('utf-8'))
        except Exception as e:
            print(f"Error sending connected clients: {e}")


def broadcast_file(sender_username, recipient_username, file_info):
    try:
        file_name, file_path = file_info.split(' ', 1)
        with open(file_path, 'rb') as file:
            file_data = file.read()
            for (sender, recipient), client_socket in active_sessions.items():
                if recipient == recipient_username:
                    client_socket.sendall(
                        f"FILE_TRANSFER:[{sender_username}] is sending a file: {file_name}".encode('utf-8'))
                    client_socket.sendall(file_data)
    except Exception as e:
        print(f"Error broadcasting file to {recipient_username}: {e}")


def establish_connection(sender_username, recipient_username):
    sender_socket = clients.get(sender_username)
    recipient_socket = clients.get(recipient_username)

    if sender_socket and recipient_socket:
        sender_socket.sendall(
            f"Connecting to {recipient_username}...".encode('utf-8'))
        recipient_socket.sendall(
            f"Connecting to {sender_username}...".encode('utf-8'))

        # Store active session
        active_sessions[(sender_username, recipient_username)] = (
            sender_socket)
        # active_sessions[(recipient_username, sender_username)] = (recipient_socket)

        sender_socket.sendall(
            f"Connection established with {recipient_username}.".encode('utf-8'))
        recipient_socket.sendall(
            f"Connection established with {sender_username}.".encode('utf-8'))
    else:
        sender_socket.sendall(
            f"User '{recipient_username}' is not connected.".encode('utf-8'))


def create_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            print("User already exists.")
            return False

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        print("User created successfully.")
        return True
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False
    finally:
        conn.close()


def authenticate_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()

    conn.close()

    return user is not None


def start_server():
    server_host = "0.0.0.0"
    server_port = 9999

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_host, server_port))
    server_socket.listen(5)

    print(f"[SERVER STARTED] Listening on {server_host}:{server_port}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client, args=(client_socket, client_address))
            client_thread.start()

    except KeyboardInterrupt:
        print("[SERVER STOPPED] Server stopped.")
        server_socket.close()


if __name__ == "__main__":
    start_server()
