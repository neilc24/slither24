"""
Single player mode (offline) for debugging.
Github: https://github.com/neilc24/slither24
"""

import pygame as pg
import math
import sys

from snake_game import SnakeGame
from config import *

# The only snake controlled by huamn existing in the offline game
MY_SNAKE_ID = "mySnake01"

# Initialize pygame
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

clock = pg.time.Clock()

mygame = SnakeGame()
mygame.add_player(MY_SNAKE_ID)
mygame.add_player("DEBUG", (2600, 3020), GREEN) # DEBUG PLAYER2

running = True
while running and (MY_SNAKE_ID in mygame.snakes):
    if mygame.snakes[MY_SNAKE_ID].speed > SPEED_NORMAL:
        pg.mixer.music.pause()
        sound_channel01.unpause()
    else:
        sound_channel01.pause()
        pg.mixer.music.unpause()

    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_p:
                mygame.snakes[MY_SNAKE_ID].length += 200 ##DEBUG
            if event.key == pg.K_o:
                mygame.snakes[MY_SNAKE_ID].length = max(LENGTH_MIN, mygame.snakes[MY_SNAKE_ID].length-200) ##DEBUG
            if event.key == pg.K_k: # DEBUG Kill player
                zf = mygame.get_zf(MY_SNAKE_ID)
                head_pos = mygame.snakes[MY_SNAKE_ID].head()
                mygame.kill_snake(MY_SNAKE_ID)
                while True:
                    for event in pg.event.get():
                        if event.type == pg.QUIT:
                            print("--- GAME OVER ---")
                            pg.mixer.music.stop()
                            pg.quit()
                            sys.exit()
                    screen.fill(BLACK)
                    mygame.render(screen=screen, head_pos=head_pos, zf=zf)
                    pg.display.flip()
                    clock.tick(FPS)
                    
    keys = pg.key.get_pressed()
    mouse_pos = pg.mouse.get_pos()

    speed = SPEED_NORMAL if not keys[pg.K_SPACE] else SPEED_FAST

    dx = mouse_pos[0]-SCREEN_CENTER[0]
    dy = mouse_pos[1]-SCREEN_CENTER[1]
    direction = math.degrees(math.atan2(-dy, dx)) # In pygame up and down are reversed

    screen.fill(BLACK)
    font = pg.font.Font(None, 36)
    text = font.render(f"{mygame.snakes[MY_SNAKE_ID]}", True, RED)
    screen.blit(text, (10, 10))
    pg.draw.circle(screen, WHITE, SCREEN_CENTER, 2, 0)
    mygame.render(screen=screen, head_pos=mygame.snakes[MY_SNAKE_ID].head(), zf=mygame.get_zf(MY_SNAKE_ID))
    pg.display.flip()

    mygame.update_player(MY_SNAKE_ID, direction, speed)
    mygame.update_player("DEBUG") # DEBUG
    mygame.update_game()

    clock.tick(FPS)

print("--- GAME OVER ---")
pg.mixer.music.stop()
pg.quit()
sys.exit()