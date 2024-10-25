"""
config.py

Config stores all the configurations needed for the game.

Github: https://github.com/neilc24/slither24
Author: Neil (GitHub: neilc24)
"""

# Network
HOST = "127.0.0.1"
PORT = 12345
PASSKEY = "sQ^w356u&9h-Jd"
RECV_TIMEOUT = 2
# Message types (int) from server to clients
MSG_TYPE_SNAKEGAME = 11  # A pickled instance of SnakeGame()
MSG_TYPE_SNAKEID = 12    # A string of snake_id
MSG_TYPE_NOTICE = 13     # Death notice
# Messages types (int) from clients to server
MSG_TYPE_PASSKEY = 21   # User register request
MSG_TYPE_INPUT = 22      # User input
MAX_PLAYERS = 100

BROADCAST_FREQUENCY = 2

# Window
FPS = 60
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SCREEN_CENTER = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
WINDOW_CAPTION = "Slither Grand Galaxy 2024"

# Music
MUSIC_VOLUME = 0.1

# Gameplay
MAP_WIDTH = 4000
MAP_HEIGHT = 4000
MAP_CENTER = (MAP_WIDTH//2, MAP_HEIGHT//2)

DIRECTION_INIT = 0 # In degrees
LENGTH_MIN = 28
SNAKE_RADIUS_MIN = 9
ANGLE_MAX = 6 # Maximum turning angle
SPEED_NORMAL = 2.4
SPEED_FAST = 4.8
SPEEDUP_COST = 0.18 # Cost of length per frame when speeding up
BODY_INTERVAL = 12.5

FOOD_PER_1000x1000 = 150
FOOD_MIN = round(FOOD_PER_1000x1000*MAP_WIDTH*MAP_HEIGHT/(1000*1000)) # Least amount of food in total
FOOD_RADIUS_AVE = 5.5 # Average normal food radius
FOOD_VALUE_AVE = 1.75 # Average normal food value

FOOD_BODY_RADIUS_AVE = SNAKE_RADIUS_MIN+2 # Average food radius made from killed snakes
FOOD_BODY_VALUE_AVE = FOOD_VALUE_AVE*3 # Average food value made from killed snakes

ZOOM_INDEX = 1.3

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)