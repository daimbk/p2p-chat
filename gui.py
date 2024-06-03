import tkinter as tk
from tkinter import filedialog, messagebox
import socket
import threading
import os


class ChatClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.geometry("250x120")
        master.title("P2P App")

        self.username = ""
        self.client_socket = None
        self.logged_in = False
        self.keep_update_running = True
        self.connected_clients = []

        self.create_widgets()

    def create_widgets(self):
        self.label_username = tk.Label(
            self.master, text="Username:")
        self.label_username.grid(row=0, column=0)

        self.entry_username = tk.Entry(self.master)
        self.entry_username.grid(row=0, column=1)

        self.label_password = tk.Label(
            self.master, text="Password:")
        self.label_password.grid(row=1, column=0)

        self.entry_password = tk.Entry(
            self.master, show="*")
        self.entry_password.grid(row=1, column=1)

        self.login_button = tk.Button(
            self.master, text="Login", command=self.login)
        self.login_button.grid(row=2, column=0, columnspan=2)

        self.create_user_button = tk.Button(
            self.master, text="Create User", command=self.create_user)
        self.create_user_button.grid(row=3, column=0, columnspan=2)

    def login(self):
        self.username = self.entry_username.get()
        password = self.entry_password.get()

        if not self.username or not password:
            messagebox.showerror(
                "Error", "Please enter both username and password.")
            return

        try:
            self.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(("127.0.0.1", 9999))

            login_attempt = f"login {self.username} {password}"
            self.client_socket.sendall(login_attempt.encode('utf-8'))

            response = self.client_socket.recv(1024).decode('utf-8')

            if response == "Login successful!":
                self.logged_in = True
                self.show_connected_clients()
            else:
                messagebox.showerror("Error", response)

        except ConnectionRefusedError:
            messagebox.showerror(
                "Error", "Connection refused. Make sure the server is running.")

    def create_user(self):
        self.username = self.entry_username.get()
        password = self.entry_password.get()

        if not self.username or not password:
            messagebox.showerror(
                "Error", "Please enter both username and password.")
            return

        try:
            self.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(("127.0.0.1", 9999))

            create_user_request = f"create_user {self.username} {password}"
            self.client_socket.sendall(create_user_request.encode('utf-8'))

            response = self.client_socket.recv(1024).decode('utf-8')

            messagebox.showinfo("Info", response)

        except ConnectionRefusedError:
            messagebox.showerror(
                "Error", "Connection refused. Make sure the server is running.")

    def show_connected_clients(self):
        self.master.withdraw()
        self.connected_clients_window = tk.Toplevel(self.master)
        self.connected_clients_window.geometry("500x400")
        self.connected_clients_window.title(
            f"Connected Clients. User: {self.username}")

        self.listbox_clients = tk.Listbox(self.connected_clients_window)
        self.listbox_clients.pack(fill=tk.BOTH, expand=True)

        self.refresh_connected_clients()

        connect_button = tk.Button(
            self.connected_clients_window, text="Connect", command=self.connect_with_client)
        connect_button.pack()

        back_button = tk.Button(
            self.connected_clients_window, text="Back", command=self.back_to_main_window)
        back_button.pack()

        threading.Thread(target=self.listen_for_updates).start()

    def refresh_connected_clients(self):
        self.client_socket.sendall("request_clients".encode('utf-8'))
        response = self.client_socket.recv(1024).decode('utf-8')
        if response.startswith("CONNECTED_CLIENTS:"):
            self.connected_clients = response.split(":")[1].split(",")
        else:
            self.connected_clients = response.split(",")

        self.listbox_clients.delete(0, tk.END)

        for client in self.connected_clients:
            self.listbox_clients.insert(tk.END, client)

    def listen_for_updates(self):
        try:
            while self.keep_update_running:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                if data.startswith("CONNECTED_CLIENTS:"):
                    self.connected_clients = data.split(":")[1].split(",")
                    self.refresh_connected_clients()
        except Exception as e:
            messagebox.showerror("Error", f"Error receiving updates: {e}")

    def connect_with_client(self):
        self.keep_update_running = False

        selected_index = self.listbox_clients.curselection()
        if not selected_index:
            messagebox.showerror("Error", "Please select a client.")
            return

        recipient_username = self.connected_clients[selected_index[0]]

        connect_request = f"connect {self.username} {recipient_username}"
        self.client_socket.sendall(connect_request.encode('utf-8'))

        communication_window = tk.Toplevel(self.master)
        communication_window.title(f"User: {self.username}")

        self.text_messages = tk.Text(communication_window)
        self.text_messages.pack(fill=tk.BOTH, expand=True)

        self.entry_message = tk.Entry(communication_window)
        self.entry_message.pack(fill=tk.BOTH, expand=True)

        send_button = tk.Button(communication_window,
                                text="Send", command=self.send_message)
        send_button.pack()

        file_button = tk.Button(communication_window,
                                text="Send File", command=self.send_file)
        file_button.pack()

        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.start()

    def receive_messages(self):
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        while True:
            data = self.client_socket.recv(1024)
            if not data:
                print("[SERVER] Connection closed by server.")
                break
            message = data.decode('utf-8')

            if message.startswith("FILE_TRANSFER:"):
                # Received a file notification
                file_info = message.split(": ")
                file_name = file_info[1]
                with open(os.path.join(downloads_folder, file_name), 'wb') as file:
                    file_data = self.client_socket.recv(1024)
                    file.write(file_data)
                print("File saved successfully.")
                # self.text_messages.insert(
                #     tk.END, f"File received successfully saved to downloads: {file_name}" + "\n")
            else:
                self.text_messages.insert(tk.END, message + "\n")

    def send_message(self):
        message = self.entry_message.get()
        if message:
            self.client_socket.sendall(f'msg {message}'.encode('utf-8'))
            self.entry_message.delete(0, tk.END)
            self.text_messages.insert(
                tk.END, f"[Me]: " + message + "\n")

    def send_file(self):
        file_path = tk.filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            self.client_socket.sendall(
                f'file {file_name} {file_path}'.encode('utf-8'))

            with open(file_path, 'rb') as file:
                while True:
                    chunk = file.read(1024)
                    if not chunk:
                        break
                    self.client_socket.sendall(chunk)
            self.text_messages.insert(
                tk.END, f"[{self.username}]: File Transferred - " + file_path + "\n")

    def back_to_main_window(self):
        self.connected_clients_window.destroy()
        self.master.deiconify()


root = tk.Tk()
app = ChatClientGUI(root)
root.mainloop()
