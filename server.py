"""
server.py

Github Repository: https://github.com/neilc24/slither24
Author: Neil (GitHub: neilc24)

pyinstaller --clean --onefile --name Slither24Server server.py
"""

import pygame as pg
import socket
import struct
import threading
from concurrent.futures import ThreadPoolExecutor
import copy

from snake_game import SnakeGame
from snake_network import SnakeNetwork
from config import *

class GameServer(SnakeNetwork):
    def __init__(self, host="", port=PORT):
        self.server_addr = (host, port)
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
            t_game.daemon = True # Set as a daemon thread
            t_game.start()

            # Loop: accepting new clients
            while True:
                # Print a snapshot of the current game
                new_client = server.accept()
                t_client = threading.Thread(target=self.handle_client, args=(new_client,))
                t_client.start()
                with self.lock_print:
                    print(f"Connected to {new_client[1]}. Connections={threading.active_count()-2}")
                with self.lock_mygame, self.lock_print:
                    print(self.mygame)

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
        if not self.send_id(player[0], new_id, lock_print=self.lock_print):
            self.remove_player(player)
            return None
        return new_id

    def remove_player(self, player, holding_lock_mygame=False, holding_lock_players=False, *, reason=None):
        """ Remove a player from the game """
        dead_id = None
        self.send_death_notice(player[0], lock_print=self.lock_print)
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
                if reason is None:
                    print(f"Player {dead_id} removed.")
                else:
                    print(f"Player {dead_id} removed. Reason: {reason}")

    def run_game(self):
        """ Run the game logic and broadcast the game state """
        i = 0
        while True:
            with self.lock_mygame:
                death_records = self.mygame.update_game()
            if len(death_records) > 0:
                with self.lock_players:
                    # If a player died remove them from {players}
                    for player in list(self.players):
                        if self.players[player] in death_records:
                            self.remove_player(player, False, True, reason="Died.")
            # Broadcast current game state to every player
            if i == BROADCAST_FREQUENCY:
                self.broadcast_game()
                i = 0
            else:
                i += 1
            self.clock.tick(FPS)

    def broadcast_game(self):
        """ Broadcast the game state to every player """
        # To decrease lock holding time, create copies
        with self.lock_mygame:
            game_snapshot = copy.deepcopy(self.mygame)
        with self.lock_players:
            copy_players = self.players.copy()
        # Using threadpool
        with ThreadPoolExecutor(max_workers=MAX_PLAYERS//2+1) as executor:
            futures = []
            for player in copy_players:
                futures.append(((executor.submit(self.send_game_snapshot, player[0], 
                                self.get_modified_snapshot(game_snapshot, copy_players[player]), 
                                lock_print=self.lock_print)), player))
            # Remove disconnected players
            for future in futures:
                if not future[0].result():
                    self.remove_player(future[1], False, False, 
                                       reason="Disconnected while broadcasting.")

    def get_modified_snapshot(self, snapshot:SnakeGame, my_snake_id):
        """ Return a "personalized" snapshot of the game """
        snapshot_copy = copy.deepcopy(snapshot)
        for snake_id in list(snapshot_copy.snakes):
            # Calculate the position of the center of the camera on the map
            zf = snapshot_copy.get_zf(my_snake_id)
            cam_center = snapshot_copy.get_cam_center(snapshot_copy.snakes[my_snake_id].head(), zf)
            if not snapshot_copy.snake_is_on_screen(snake_id, cam_center, zf):
                del snapshot_copy.snakes[snake_id]
        return snapshot_copy

    def handle_client_msg(self, snake_id, raw_msg):
        """ Handle raw data received from a client """
        raw_data, msg_type = raw_msg
        if msg_type == MSG_TYPE_INPUT:
            direction, speed = struct.unpack('ff', raw_data)
            speed = round(speed, 4)
            with self.lock_mygame:
                if snake_id in self.mygame.snakes:
                    self.mygame.update_player(snake_id, direction, speed)
        elif msg_type == MSG_TYPE_PASSKEY:
            pass #
        else:
            with self.lock_print:
                print("Unknown type of message from client.")
    
    def is_passkey(self, raw_msg):
        raw_data, msg_type = raw_msg
        return msg_type == MSG_TYPE_PASSKEY and raw_data.decode('utf-8') == PASSKEY

    def handle_client(self, player):
        """ Register client and receive messages"""
        with player[0] as conn:
            # Receive and recognize passkey
            msg = self.recv_msg(conn, lock_print=self.lock_print)
            if msg is None or not self.is_passkey(msg):
                with self.lock_print:
                    print(f"Invalid passkey from {player[1]}")
                return
            # Register player
            client_id = self.register_player(player)
            # Message receiving loop
            while True:
                raw_msg = self.recv_msg(conn, lock_print=self.lock_print)
                if raw_msg is None:
                    break
                self.handle_client_msg(client_id, raw_msg)
            # Remove player in the end
            self.remove_player(player, False, False, reason="Disconnected while receiving msg.")

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