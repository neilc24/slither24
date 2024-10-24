"""
client.py

A client program for the Slither24 multiplayer game. This client connects to the server,
receives game state updates, and allows the player to interact with the game using pygame.
The client handles receiving data from the server, user input, and rendering the game screen.

GitHub Repository: https://github.com/neilc24/slither24
Author: Neil (GitHub: neilc24)

pyinstaller --clean --onefile --name SlitherGrandGalaxy24 
            --icon assets/icon.ico --add-data assets:assets client.py
"""

import pygame as pg
import math
import socket
import pickle
import threading

from snake_game import SnakeGame
from snake_network import SnakeNetwork
from config import *

class GameClient(SnakeNetwork):
    def __init__(self, host=HOST, port=PORT):
        self.server_addr = (host, port)
        self.game_img = SnakeGame() # A local image of the game that runs on the server
        self.my_id = ""
        self.lock_game_img = threading.Lock()
        self.lock_print = threading.Lock()
        self.id_recv_event = threading.Event()
        self.game_img_recv_event = threading.Event()
        self.stop_event = threading.Event()
        self.clock = pg.time.Clock()

    def start(self):
        """ Start game """
        screen, sound_channel = my_client.init_window()
        # Ask user for server address
        self.input_addr_shell()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
            # Connect to server
            with self.lock_print:
                print(f"Connecting to {self.server_addr}...")
            conn.settimeout(RECV_TIMEOUT*2)
            try:
                conn.connect(self.server_addr)
            except Exception as e:
                with self.lock_print:
                    print(f"Cannot connect. Reason: {e}")
                    return
            with self.lock_print:
                print("Connected to server.")
            # Start a thread to receive data from server
            t_receive = threading.Thread(target=self.handle_server, args=(conn,))
            t_receive.daemon = True # Set as a daemon thread
            t_receive.start()
            # Wait till received my_id from server
            self.id_recv_event.wait()
            # Wait untill receiving first game_img
            self.game_img_recv_event.wait()
            pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SHOWN)
            # Game loop
            while not self.stop_event.is_set() and self.game_loop(screen, sound_channel, conn):
                self.clock.tick(FPS)
            with self.lock_print:
                print("-- GAME OVER --")
        my_client.quit_window()
    
    def init_window(self):
        """ Initialize music and window display """
        # Initialize pygame
        pg.init()
        # Initialize music player
        pg.mixer.init()
        pg.mixer.music.set_volume(MUSIC_VOLUME) # Set volume
        pg.mixer.music.load(self.get_abs_path('assets/music01.mp3'))
        pg.mixer.music.play(-1)
        pg.mixer.music.pause()
        # Initialize sound effect channel
        sound_channel = pg.mixer.Channel(0)
        sound_channel.set_volume(MUSIC_VOLUME) # Set volume
        speedup_sound = pg.mixer.Sound(self.get_abs_path('assets/sound_effect01.mp3'))
        sound_channel.play(speedup_sound, loops=-1)
        sound_channel.pause()
        # Set up window display
        pg.display.set_icon(pg.image.load(self.get_abs_path('assets/icon.png')))
        pg.display.set_caption(WINDOW_CAPTION)
        screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pg.HIDDEN)
        return screen, sound_channel

    def quit_window(self):
        """ Quit pygame and music mixer """
        pg.mixer.quit()
        pg.quit()

    def input_addr_shell(self):
        """ Get server address from user input """
        with self.lock_print:
            user_input = input("Enter server address (Ip:Port):")
        results = tuple(user_input.split(":"))
        host, port = results[0], ""
        if len(results) > 1:
            port = results[1]
        if host != "":
            self.server_addr = (host, self.server_addr[1])
        if port != "" and port.isdigit():
            self.server_addr = (self.server_addr[0], int(port))
        return self.server_addr

    def game_loop(self, screen, sound_channel, conn):
        """ Main game loop inside 'while Ture' """
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return False

        # Switch music if speeding up
        if self.game_img.snakes[self.my_id].speed > SPEED_NORMAL:
            pg.mixer.music.pause()
            sound_channel.unpause()
        else:
            sound_channel.pause()
            pg.mixer.music.unpause()

        # Get user input (direction and speed) and send to server
        keys, mouse_pos = pg.key.get_pressed(), pg.mouse.get_pos()
        dx, dy = mouse_pos[0]-SCREEN_CENTER[0], mouse_pos[1]-SCREEN_CENTER[1]
        direction = math.degrees(math.atan2(-dy, dx))
        speed = SPEED_NORMAL if not keys[pg.K_SPACE] else SPEED_FAST
        # Send input to server
        if not self.send_input(conn, direction, speed, lock_print=self.lock_print):
            return False

        # Render
        screen.fill(BLACK)
        font = pg.font.Font(None, 36)
        text = font.render(f"{self.game_img.snakes[self.my_id]}", True, RED)
        screen.blit(text, (10, 10))
        pg.draw.line(screen, WHITE, SCREEN_CENTER, mouse_pos, width=1)
        self.game_img.render(screen=screen, 
                             head_pos=self.game_img.snakes[self.my_id].head(), 
                             zf=self.game_img.get_zf(self.my_id))
        pg.display.flip()

        return True

    def handle_server_data(self, raw_data, msg_type):
        """ Handle raw data received from server """
        if msg_type == MSG_TYPE_SNAKEGAME:
            with self.lock_game_img:
                self.game_img = pickle.loads(raw_data)
                if not self.game_img_recv_event.is_set():
                    with self.lock_print:
                        print(f"Received first game snapshot={self.game_img}")
                    self.game_img_recv_event.set()
        elif msg_type == MSG_TYPE_SNAKEID:
            self.my_id = raw_data.decode()
            with self.lock_print:
                print(f"Received id={self.my_id}")
            self.id_recv_event.set()
        elif msg_type == MSG_TYPE_NOTICE:
            with self.lock_print:
                print("Received message: You died.")
            self.stop_event.set()
        else:
            with self.lock_print:
                print("Cannot decode data from server.")

    def handle_server(self, conn):
        """ Receive data from the server """
        with conn:
            while not self.stop_event.is_set():
                msg = self.recv_msg(conn, lock_print=self.lock_print)
                if msg is None:
                    break
                raw_data, msg_type = msg
                self.handle_server_data(raw_data, msg_type)
        self.stop_event.set()

if __name__ == "__main__":
    my_client = GameClient()
    my_client.start()