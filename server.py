"""
Server of the game without graphics.
Github: https://github.com/neilc24/slither24
"""

import pygame as pg
import socket
import pickle
import struct
import threading

from snake_game import SnakeGame
from config import *

HOST = ""
PORT = 12346

class GameServer():
    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.mygame = SnakeGame()
        self.players = {}
        self.lock_mygame = threading.Lock()
        self.lock_players = threading.Lock()
        self.lock_print = threading.Lock()
        self.clock = pg.time.Clock()

    def start(self):
        """ Start server """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            try:
                server.bind((self.host, self.port))
            except:
                with self.lock_print:
                    print("Error:Cannot start server.")
                    return
            server.listen()
            with self.lock_print:
                print(f"Server listening on {self.host}:{self.port}...")

            # Start a new thread to run game logic and broadcast
            t_game = threading.Thread(target=self.run_game)
            t_game.start()

            # Loop: accepting new clients
            while True:
                new_client = server.accept()
                t_client = threading.Thread(target=self.handle_client, args=(new_client,))
                t_client.start()
                with self.lock_print:
                    print(f"Connected to {new_client[1]}. Connections={threading.active_count()-2}")

    def register_player(self, player):
        """ Register a new player in the game and return their ID """
        new_id = self.generate_id(player[1][0])
        # Add player to players
        with self.lock_players:
            self.players[player] = new_id
        # Add player to mygame
        with self.lock_mygame:
            self.mygame.add_player(new_id, color=self.mygame.randcolor(100, 255))
        with self.lock_print:
            print(f"New player added. ID={new_id}")
        # Send ID back to player
        self.send_id(player)
        return new_id

    def remove_player(self, player):
        """ Remove a player from the game """
        dead_id = self.players[player]
        # Remove player from mygame
        with self.lock_mygame:
            if dead_id in self.mygame.snakes:
                del self.mygame.snakes[dead_id]
        # Remove player from players
        with self.lock_players:
            if player in self.players:
                del self.players[player]
        with self.lock_print:
            print(f"Player removed. ID={dead_id}")

    def run_game(self):
        """ Run the game logic and broadcast the game state """
        while True:
            with self.lock_mygame:
                self.mygame.update_game()
                with self.lock_players:
                    # If a player died remove them from {players}
                    for player in list(self.players):
                        if not self.players[player] in self.mygame.snakes:
                            self.send_death_notice(player)
                            self.remove_player(player)
            # Broadcast current game state to every player
            self.broadcast_game()
            self.clock.tick(FPS)

    def broadcast_game(self):
        with self.lock_mygame:
            data_to_send = pickle.dumps(self.mygame)
        for player in self.players:
            try:
                # Send header first including message type and length of the data
                player[0].sendall(struct.pack('!II', MSG_TYPE_SNAKEGAME, len(data_to_send)))
                # Send data
                player[0].sendall(data_to_send)
            except:
                with self.lock_print:
                    print(f"Connection with {player[1]} interrupted.")
                self.remove_player(player) # Remove player

    def generate_id(self, ip="unknown"):
        """ Generate an ID for a new player """
        for i in range(1, MAX_PLAYERS):
            if not f"{ip}_{i}" in self.mygame.snakes:
                return f"{ip}_{i}"
        return None

    def send_id(self, player):
        """ Send player their ID """
        data_to_send = self.players[player].encode()
        try:
            player[0].sendall(struct.pack('!II', MSG_TYPE_SNAKEID, len(data_to_send))) # Header
            player[0].sendall(data_to_send)
        except:
            self.remove_player(player)
            return False
        return True

    def send_death_notice(self, player):
        """ Send a message to notice player that they died """
        try:
            player[0].sendall(struct.pack('!II', MSG_TYPE_NOTICE, 0)) # Header
            # No following data after header
        except:
            with self.lock_print:
                print(f"Connection with {player[1]} interrupted.")
            self.remove_player(player)

    def handle_client_data(self, snake_id, raw_data, msg_type):
        """ Handle raw data received from a client """
        if msg_type == MSG_TYPE_INPUT:
            direction, speed = struct.unpack('ff', raw_data)
            speed = round(speed, 4)
            with self.lock_mygame:
                if snake_id in self.mygame.snakes:
                    self.mygame.update_player(snake_id, direction, speed)
        else:
            # Unknown message type
            pass

    def recv_all(self, conn, l):
        """ Receive all data of length l"""
        data = b''
        while len(data) < l:
            packet = conn.recv(l - len(data))
            if not packet:
                return None
            data += packet
        return data

    def handle_client(self, player):
        """ Register client and receive messages"""
        with player[0]:
            # Register player
            client_id = self.register_player(player)
            # Message receiving loop
            while True:
                raw_header = self.recv_all(player[0], 8)
                if raw_header is None:
                    break
                msg_type, msg_len = struct.unpack('!II', raw_header)
                raw_data = self.recv_all(player[0], msg_len)
                if raw_data is None:
                    break
                self.handle_client_data(client_id, raw_data, msg_type)
            # Remove player in the end
            self.remove_player(player)

if __name__ == "__main__":
    my_server = GameServer()
    my_server.start()