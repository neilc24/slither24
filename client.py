"""
client.py
Github: https://github.com/neilc24/slither24
"""

import pygame as pg
import math
import socket
import pickle
import threading

from snake_game import SnakeGame
from snake_network import *
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
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
            # Connect to server
            try:
                conn.connect(self.server_addr)
            except Exception as e:
                with self.lock_print:
                    print(f"Cannot connect to {self.server_addr}, Reason: {e}")
                    return #
            with self.lock_print:
                print("Connected to server.")

            # Start a thread to receive data from server
            t_receive = threading.Thread(target=self.handle_server, args=(conn,))
            t_receive.start()

            # Wait till received my_id from server
            self.id_recv_event.wait()
            # Wait untill receiving first game_img
            self.game_img_recv_event.wait()

            # Initialize pygame
            pg.init()
            # Initialize music player
            pg.mixer.init()
            pg.mixer.music.set_volume(MUSIC_VOLUME) # Set volume
            pg.mixer.music.load('assets/music01.mp3')
            pg.mixer.music.play(-1)
            # Initialize sound effect channel
            speedup_sound = pg.mixer.Sound('assets/sound_effect01.mp3')
            sound_channel = pg.mixer.Channel(0)
            sound_channel.set_volume(MUSIC_VOLUME) # Set volume
            sound_channel.play(speedup_sound, loops=-1)
            sound_channel.pause()
            # Set up window display
            pg.display.set_icon(pg.image.load('assets/icon.png'))
            screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pg.display.set_caption(WINDOW_CAPTION)
            
            # Game loop
            while not self.stop_event.is_set() and self.game_loop(screen, sound_channel, conn):
                self.clock.tick(FPS)
            
            with self.lock_print:
                print("GAME OVER")
            # Clean up and quit
            pg.mixer.music.stop()
            pg.quit()

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
        if not self.send_input(conn, direction, speed):
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
                msg = self.recv_msg(conn)
                if msg is None:
                    break
                raw_data, msg_type = msg
                self.handle_server_data(raw_data, msg_type)
        self.stop_event.set()
    
def window_input_server_addr():
    """ Get server address for user input on a GUI"""
    pg.init()
    pg.display.set_icon(pg.image.load('assets/icon.png'))
    pg.display.set_caption(WINDOW_CAPTION)
    screen = pg.display.set_mode((400, 200))
    font = pg.font.Font(None, 32)
    user_input = ""
    input_active = True
    clock = pg.time.Clock()
    while input_active:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                return None
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_RETURN:  # Enter key pressed
                    input_active = False  # Stop input
                elif event.key == pg.K_BACKSPACE:  # Backspace key
                    user_input = user_input[:-1]  # Remove last character
                else:
                    user_input += event.unicode  # Add new character
        screen.fill(BLACK)
        screen.blit(font.render("Ender server address (ip:port):", True, WHITE), (10, 10))

        input_box = pg.Rect(100, 70, 200, 45)  # Position and size of input box
        pg.draw.rect(screen, WHITE, input_box, 2)  # Draw the box border

        text_surface = font.render(user_input, True, WHITE)
        screen.blit(text_surface, (input_box.x + 10, input_box.y + 10))
        pg.display.flip()
        clock.tick(30)
    
    pg.quit()
    if user_input == "":
        return (HOST, PORT)
    results = tuple(user_input.split(":"))
    if len(results) != 2 or (not results[1].isdigit() and results[1] != ""):
        return None
    host, port = results[0], results[1]
    if host == "":
        host = HOST
    if port == "":
        port = PORT
    else:
        port = int(port)
    return (results[0], results[1])

if __name__ == "__main__":
    #s = window_input_server_addr()
    #if s is None:
    #    print("Invalid address.")
    #    sys.exit()
    my_client = GameClient()
    my_client.start()