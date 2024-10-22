# config.py
# Neil 2024

# Window
FPS = 60
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SCREEN_CENTER = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
WINDOW_CAPTION = "Slither Grand Galaxy 2024"

# Gameplay
MAP_WIDTH = 6000
MAP_HEIGHT = 6000
MAP_CENTER = (MAP_WIDTH//2, MAP_HEIGHT//2)

DIRECTION_INIT = 0 # In degrees
LENGTH_MIN = 28
SNAKE_RADIUS_MIN = 9
ANGLE_MAX = 7 # Maximum turning angle
SPEED_NORMAL = 2.4
SPEED_FAST = 5.6
SPEEDUP_COST = 0.16 # Cost of length per frame when speeding up

FOOD_MIN = 6000 # Least amount of food in total
FOOD_RADIUS_AVE = 5.5 # Average normal food radius
FOOD_VALUE_AVE = 1.75 # Average normal food value

FOOD_BODY_RADIUS_AVE = SNAKE_RADIUS_MIN+2 # Average food radius made from killed snakes
FOOD_BODY_VALUE_AVE = 8 # Average food value made from killed snakes

BODY_INTERVAL = 12.5

MAX_PLAYERS = 200

# Network
# Messages from server to clients
MSG_TYPE_SNAKEGAME = 11  # A pickled instance of SnakeGame()
MSG_TYPE_SNAKEID = 12    # A string of snake_id
MSG_TYPE_NOTICE = 13     # Death notice
# Messages from a client to server
MSG_TYPE_INPUT = 21      # User input

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)