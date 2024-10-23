"""
server.py
Github: https://github.com/neilc24/slither24
"""

import pygame as pg
import socket
import struct
import threading
from concurrent.futures import ThreadPoolExecutor

from snake_game import SnakeGame
from snake_network import *
from config import *

class GameServer(SnakeNetwork):
    def __init__(self):
        self.server_addr = (HOST, PORT)
        self.mygame = SnakeGame()
        self.players = {}
        # Deadlock prevention: lock_mygame > lock_players > lock_print
        self.lock_mygame = threading.Lock()
        self.lock_players = threading.Lock()
        self.lock_print = threading.Lock()
        self.clock = pg.time.Clock()

    def start(self):
        """ Start server """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            try:
                server.bind(self.server_addr)
            except Exception as e:
                with self.lock_print:
                    print(f"Error: Cannot start server ({e})")
                return

            server.listen()
            with self.lock_print:
                print(f"Server listening on {self.server_addr}...")

            # Start a new thread to run game logic and broadcast
            t_game = threading.Thread(target=self.run_game)
            t_game.start()

            # Loop: accepting new clients
            while True:
                # Print a snapshot of the current game
                with self.lock_mygame, self.lock_print:
                    print(self.mygame)
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
        if not self.send_id(player[0], new_id):
            self.remove_player(player)
            return None
        return new_id

    def remove_player(self, player, holding_lock_mygame=False, holding_lock_players=False):
        """ Remove a player from the game """
        dead_id = None
        self.send_death_notice(player[0])
        # Close socket connection
        player[0].close()
         # Remove player from self.players
        if not holding_lock_players:
            self.lock_players.acquire()
        if player in self.players:
            dead_id = self.players[player]
            del self.players[player]
        if not holding_lock_players:
            self.lock_players.release()
        # Remove player from self.mygame
        if not holding_lock_mygame:
            self.lock_mygame.acquire()
        if dead_id in self.mygame.snakes:
            self.mygame.kill_snake(dead_id)
        if not holding_lock_mygame:
            self.lock_mygame.release()
        # Print
        if not dead_id is None:
            with self.lock_print:
                print(f"Player {dead_id} removed.")

    def run_game(self):
        """ Run the game logic and broadcast the game state """
        while True:
            with self.lock_mygame:
                death_records = self.mygame.update_game()
            if len(death_records) > 0:
                with self.lock_players:
                    # If a player died remove them from {players}
                    for player in list(self.players):
                        if self.players[player] in death_records:
                            self.remove_player(player, holding_lock_mygame=False, holding_lock_players=True)
            # Broadcast current game state to every player
            self.broadcast_game()
            self.clock.tick(FPS)

    def broadcast_game(self):
        """ Broadcast the game state to every player """
        # Using threadpool
        with ThreadPoolExecutor(max_workers=MAX_PLAYERS//2+1) as executor:
            with self.lock_mygame, self.lock_players:
                futures = [executor.submit(self.send_game_snapshot, player[0], self.mygame) for player in self.players]
                for i in range(0, len(self.players)):
                    if not futures[i]:
                        self.remove_player(self.players[i], True, True)

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

    def handle_client(self, player):
        """ Register client and receive messages"""
        with player[0] as conn:
            # Register player
            client_id = self.register_player(player)
            # Message receiving loop
            while True:
                msg = self.recv_msg(conn)
                if msg is None:
                    break
                raw_data, msg_type = msg
                self.handle_client_data(client_id, raw_data, msg_type)
            # Remove player in the end
            self.remove_player(player, holding_lock_mygame=False, holding_lock_players=False)

    def generate_id(self, ip="unknown"):
        """ Generate an ID for a new player """
        with self.lock_mygame:
            for i in range(1, MAX_PLAYERS):
                if not f"{ip}_{i}" in self.mygame.snakes:
                    return f"{ip}_{i}"
        return None
    
if __name__ == "__main__":
    my_server = GameServer()
    my_server.start()