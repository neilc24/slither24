# client.py
# Neil 2024

import pygame as pg
import math
import socket
import pickle
import struct
import threading
from snake_game import SnakeGame
from config import *

# HOST = "165.227.82.177"
HOST = "127.0.0.1"
PORT = 12346

# A local image of the game that runs on the server and its access lock
game_img = SnakeGame()
lock_gameimg = threading.Lock()
# My snake_id remains unknown untill received from server
my_id = ""
# Threading lock for commandline printing
lock_print = threading.Lock()

clock = pg.time.Clock()

# Create an event of receiving snake_id from server
id_received_event = threading.Event()
# For signaling the first received game_img
img_received_event = threading.Event()

# Handle raw data received from server
def handle_data_client(raw_data, msg_type):
    if msg_type == MSG_TYPE_SNAKEGAME:
        with lock_gameimg:
            global game_img
            game_img = pickle.loads(raw_data)
        with lock_print:
            print(game_img) # DEBUG
        img_received_event.set()
    elif msg_type == MSG_TYPE_SNAKEID:
        global my_id
        my_id = raw_data.decode()
        # Send a event signaling the main thread
        id_received_event.set()
    elif msg_type == MSG_TYPE_NOTICE:
        with lock_print:
            print("You died.")
        # ...
    else:
        with lock_print:
            print("Can't decode message from server.")

# Receive all data of length l
def recv_all(server, l):
    data = b""
    while len(data) < l:
        packet = server.recv(l-len(data))
        if not packet:
            return None
        data += packet
    return data

# Function to receive data from the server
def receive_data(s):
    while True:
        raw_header = recv_all(s, 8)
        if not raw_header:
            return 
        msg_type, msg_len = struct.unpack('!II', raw_header)
        raw_data = recv_all(s, msg_len)
        if not raw_data:
            return
        handle_data_client(raw_data, msg_type)

# Send input message to server
def send_input(s, direction, speed):
    data_to_send = struct.pack("ff", direction, speed)
    try:
        # Send header
        s.sendall(struct.pack('!II', MSG_TYPE_INPUT, len(data_to_send)))
        # Send data
        s.sendall(data_to_send)
    except:
        return False
    return True

# The main game loop inside "while True"
def game_loop(screen, sound_channel, server):
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
    if not send_input(server, direction, speed):
        with lock_print:
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

def start_game_client():
    # Try to connect to server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
        except:
            with lock_print:
                print("Cannot connect.")
                return
        with lock_print:
            print("Connected to server.")

        # Start a thread to receive data from server
        t_receive = threading.Thread(target=receive_data, args=(s,))
        t_receive.start()

        # Wait till received my_id from server
        id_received_event.wait()
        with lock_print:
            print("Received id={my_id}")

        # Wait untill receiving first game_img
        img_received_event.wait()
        with lock_print:
            print("Starting game...")
        
        # Initialize pygame
        pg.init()
        # Initialize music player
        pg.mixer.init()
        # Load music
        pg.mixer.music.load('assets/music01.mp3')
        pg.mixer.music.play(-1)
        speedup_sound = pg.mixer.Sound('assets/sound_effect01.mp3')
        sound_channel01 = pg.mixer.Channel(0)
        sound_channel01.play(speedup_sound, loops=-1)
        sound_channel01.pause()
        # Set up window display
        pg.display.set_icon(pg.image.load('assets/icon.png'))
        screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption(WINDOW_CAPTION)
        
        while game_loop(screen=screen, sound_channel=sound_channel01, server=s):
            clock.tick(FPS)
        
        # Quit music mixer and pygame
        pg.mixer.music.stop()    
        pg.quit()

if __name__ == "__main__":
    print("-- "+WINDOW_CAPTION+" --")
    start_game_client()