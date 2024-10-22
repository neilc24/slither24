# server.py
# Neil 2024

import pygame as pg
import socket
import pickle
import struct
import threading
from snake_game import SnakeGame
from config import *

HOST = ""
PORT = 12346

# Define mygame and its threading lock
mygame = SnakeGame()
lock_mygame = threading.Lock()
# Define players and its threading lock
players = {} # {(socket, addr): snake_id)}
lock_players = threading.Lock()
# Threading lock for commandline printing
lock_print = threading.Lock()

clock = pg.time.Clock()

# Send game state to all clients
def broadcast_game():
    with lock_mygame:
        data_to_send = pickle.dumps(mygame)
    for player in players:
        try:
            # Send header first including message type and length of the data
            player[0].sendall(struct.pack('!II', MSG_TYPE_SNAKEGAME, len(data_to_send)))
            # Send data
            player[0].sendall(data_to_send)
        except:
            with lock_print:
                print(f"Connection with {player[1]} interrupted.")
            # ...

# Run the game logic
def run_game():
    while True:
        with lock_mygame:
            mygame.update_game()
        # Broadcate current game state to every player
        broadcast_game()
        clock.tick(FPS)

# Remove a client from clients
def remove_client(conn, addr):
    if (conn, addr) in players:
        with lock_players:
            players.remove((conn, addr))

# Handle raw data received from a client
def handle_data_server(snake_id, raw_data, msg_type):
    if msg_type == MSG_TYPE_INPUT:
        direction, speed = struct.unpack('ff', raw_data)
        speed = round(speed, 4)
        with lock_mygame:
            mygame.update_player(snake_id, direction, speed)

# Send snake_id to player
def send_id(conn, snake_id):
    conn.sendall(struct.pack('!II', MSG_TYPE_SNAKEID, len(snake_id)))
    conn.sendall(snake_id.encode())

# Generate a snake_id for a new player
def generate_id(ip):
    for i in range(1, MAX_PLAYERS):
        if not f"{ip}_{i}" in mygame.snakes:
            return f"{ip}_{i}"
    return False

def recv_all(server, l):
    data = b''
    while len(data) < l:
        packet = server.recv(l - len(data))
        if not packet:
            return None
        data += packet
    return data

# Get messages from a client
def handle_client(conn, addr):
    with conn:
        # Add a new player using and generate a new snake_id
        client_id = generate_id(addr[0])
        # Add player to mygame
        with lock_mygame:
            mygame.add_player(client_id, color=mygame.randcolor(100, 220))
        # Register id to players
        with lock_players:
            players[(conn, addr)] = client_id
        send_id(conn, client_id)
        with lock_print:
            print(f"New player added. ID={client_id}")

        is_connected = True
        while is_connected:
            raw_header = recv_all(conn, 8)
            if not raw_header:
                return
            msg_type, msg_len = struct.unpack('!II', raw_header)
            raw_data = recv_all(conn, msg_len)
            if not raw_data:
                return
            handle_data_server(client_id, raw_data, msg_type)

# Handle new client connections
def start_server():
    # Start game
    t_game = threading.Thread(target=run_game)
    t_game.start()

    # Start accepting connections from clients
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        with lock_print:
            print(f"Server listening on {HOST}:{PORT}...")

        while True:
            new_client = server.accept()
            with lock_players:
                players[new_client] = ""
            t_client = threading.Thread(target=handle_client, args=new_client)
            t_client.start()
            with lock_print:
                print(f"Connected to {new_client[1]}. Active connections:{threading.active_count()-2}")

if __name__ == "__main__":
    start_server()