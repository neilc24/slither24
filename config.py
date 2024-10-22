"""
Config stores all the configurations needed for the game.
Github: https://github.com/neilc24/slither24
"""

# Window
FPS = 60
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SCREEN_CENTER = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
WINDOW_CAPTION = "Slither Grand Galaxy 2024"

# Music
MUSIC_VOLUME = 0.1

# Gameplay
MAP_WIDTH = 3000
MAP_HEIGHT = 3000
MAP_CENTER = (MAP_WIDTH//2, MAP_HEIGHT//2)

DIRECTION_INIT = 0 # In degrees
LENGTH_MIN = 28
SNAKE_RADIUS_MIN = 9
ANGLE_MAX = 6 # Maximum turning angle
SPEED_NORMAL = 2.4
SPEED_FAST = 5.6
SPEEDUP_COST = 0.16 # Cost of length per frame when speeding up

FOOD_MIN = 4000 # Least amount of food in total
FOOD_RADIUS_AVE = 5.5 # Average normal food radius
FOOD_VALUE_AVE = 1.75 # Average normal food value

FOOD_BODY_RADIUS_AVE = SNAKE_RADIUS_MIN+2 # Average food radius made from killed snakes
FOOD_BODY_VALUE_AVE = FOOD_VALUE_AVE*3 # Average food value made from killed snakes

BODY_INTERVAL = 12.5

MAX_PLAYERS = 200

# Network
# Message types (int) from server to clients
MSG_TYPE_SNAKEGAME = 11  # A pickled instance of SnakeGame()
MSG_TYPE_SNAKEID = 12    # A string of snake_id
MSG_TYPE_NOTICE = 13     # Death notice
# Messages types (int) from clients to server
MSG_TYPE_INPUT = 21      # User input

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)