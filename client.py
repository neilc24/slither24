"""
Client of the game.
Github: https://github.com/neilc24/slither24
"""

import pygame as pg
import math
import socket
import pickle
import struct
import threading
import sys

from snake_game import SnakeGame
from config import *

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 12345

class GameClient():
    def __init__(self, host, port):
        self.server_addr = (host, port)
        self.game_img = SnakeGame() # A local image of the game that runs on the server
        self.my_id = ""
        self.is_alive = False
        self.lock_game_img = threading.Lock()
        self.lock_print = threading.Lock()
        self.id_recv_event = threading.Event()
        self.game_img_recv_event = threading.Event()
        self.clock = pg.time.Clock()

    def start(self):
        """ Start game """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            # Connect to server
            try:
                server_socket.connect(self.server_addr)
            except:
                with self.lock_print:
                    print(f"Cannot connect to {self.server_addr}")
                    return #
            with self.lock_print:
                print("Connected to server.")

            # Start a thread to receive data from server
            t_receive = threading.Thread(target=self.receive_data, args=(server_socket,))
            t_receive.start()

            # Wait till received my_id from server
            self.id_recv_event.wait()
            with self.lock_print:
                print(f"Received id={my_id}")

            # Wait untill receiving first game_img
            self.game_img_recv_event.wait()
            with self.lock_print:
                print("Starting game...")

            # Mark self as alive
            global is_alive
            is_alive = True
            
            # Initialize pg
            pg.init()
            # Initialize music player
            pg.mixer.init()
            # Load music
            pg.mixer.music.load('assets/music01.mp3')
            pg.mixer.music.play(-1)
            pg.mixer.music.set_volume(MUSIC_VOLUME) # Set volume
            speedup_sound = pg.mixer.Sound('assets/sound_effect01.mp3')
            sound_channel01 = pg.mixer.Channel(0)
            sound_channel01.play(speedup_sound, loops=-1)
            sound_channel01.set_volume(MUSIC_VOLUME) # Set volume
            sound_channel01.pause()
            # Set up window display
            pg.display.set_icon(pg.image.load('assets/icon.png'))
            screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pg.display.set_caption(WINDOW_CAPTION)
            
            while self.game_loop(screen=screen, sound_channel=sound_channel01, server=server_socket) and is_alive:
                self.clock.tick(FPS)
            
            self.close()

    def close(self):
        """ End the whole program """
        pg.mixer.music.stop()
        pg.quit()
        sys.exit()

    def game_loop(self, screen, sound_channel, server):
        """ Main game loop inside 'while Ture' """
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return False

        # Switch music if speeding up
        if game_img.snakes[my_id].speed > SPEED_NORMAL:
            pg.mixer.music.pause()
            sound_channel.unpause()
        else:
            sound_channel.pause()
            pg.mixer.music.unpause()

        # Get user input (direction and speed) and sent it to server
        keys = pg.key.get_pressed()
        mouse_pos = pg.mouse.get_pos()
        dx, dy = mouse_pos[0]-SCREEN_CENTER[0], mouse_pos[1]-SCREEN_CENTER[1]
        direction = math.degrees(math.atan2(-dy, dx))
        speed = SPEED_NORMAL if not keys[pg.K_SPACE] else SPEED_FAST

        # Send input to server
        if not self.send_input(server, direction, speed):
            with self.lock_print:
                print("Connection interrupted.")
            return False

        # Render
        screen.fill(BLACK)
        font = pg.font.Font(None, 36)
        text = font.render(f"{game_img.snakes[my_id]}", True, RED)
        screen.blit(text, (10, 10))
        pg.draw.line(screen, WHITE, SCREEN_CENTER, mouse_pos, width=1)
        pg.draw.circle(screen, WHITE, SCREEN_CENTER, 2, 0)
        game_img.render(screen=screen, head_pos=game_img.snakes[my_id].head(), zf=game_img.get_zf(my_id))
        pg.display.flip()

        return True

    def handle_server_data(self, raw_data, msg_type):
        """ Handle raw data received from server """
        if msg_type == MSG_TYPE_SNAKEGAME:
            with self.lock_game_img:
                global game_img
                game_img = pickle.loads(raw_data)
            self.game_img_recv_event.set()
        elif msg_type == MSG_TYPE_SNAKEID:
            global my_id
            my_id = raw_data.decode()
            self.id_recv_event.set()
        elif msg_type == MSG_TYPE_NOTICE:
            with self.lock_print:
                print("You died.") # DEBUG
            global is_alive
            is_alive = False
            self.close()
        else:
            pass
    
    def recv_all(self, server, l):
        """ Receive length l of data """
        data = b""
        while len(data) < l:
            packet = server.recv(l-len(data))
            if not packet:
                return None
            data += packet
        return data

    def receive_data(self, s):
        """ Receive data from the server """
        while True:
            raw_header = self.recv_all(s, 8)
            if not raw_header:
                self.close() # Connection interrupted
                return #
            msg_type, msg_len = struct.unpack('!II', raw_header)
            raw_data = b""
            if not msg_type == MSG_TYPE_NOTICE:
                raw_data = self.recv_all(s, msg_len)
                if not raw_data:
                    self.close() # Connection interruped
                    return #
            self.handle_server_data(raw_data, msg_type)

    def send_input(self, s, direction, speed):
        """ Send input message to server """
        data_to_send = struct.pack("ff", direction, speed)
        try:
            # Send header
            s.sendall(struct.pack('!II', MSG_TYPE_INPUT, len(data_to_send)))
            # Send data
            s.sendall(data_to_send)
        except:
            return False
        return True
    
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
        return (DEFAULT_HOST, DEFAULT_PORT)
    results = tuple(user_input.split(":"))
    if len(results) != 2 or (not results[1].isdigit() and results[1] != ""):
        return None
    host, port = results[0], results[1]
    if host == "":
        host = DEFAULT_HOST
    if port == "":
        port = DEFAULT_PORT
    else:
        port = int(port)
    return (results[0], results[1])

if __name__ == "__main__":
    s = window_input_server_addr()
    if s is None:
        print("Invalid address.")
        sys.exit()
    my_client = GameClient(s[0], s[1])
    my_client.start()