"""
snake_game.py

Including main class SnakeGame.

Github: https://github.com/neilc24/slither24
Author: Neil (GitHub: neilc24)
"""

import pygame as pg
import math
import random

from snake import Snake
from config import *
     
class SnakeGame:
    def __init__ (self):
        # self.snakes = {Snake()}
        self.snakes = {}
        # self.food = {pos:{"color":GREEN, "radius":5, "value":1.0}}
        self.food = {}

    def __str__ (self):
        return f"<SnakeGame snakes={len(self.snakes)}, food={len(self.food)}>"
    
    def randcolor(self, low_brightness = 0, high_brightness = 255):
        """ Return a random RGB color """
        l, h = max(low_brightness, 0), min(high_brightness, 255)
        return (random.randint(l, h), random.randint(l, h), random.randint(l, h))
    
    def vibrate_pos(self, pos, factor=1):
        """ Return a position that's slightly differnt from the original one """
        r1, r2 = random.random()-0.5, random.random()-0.5
        return (round(pos[0]+r1*factor), round(pos[1]+r2*factor))
    
    def vibrate_color(self, color, negative, positive):
        """ Adjust the color to make it slightly different """
        vibrate_rgb = lambda x: max(0, min(255, x+random.randint(negative, positive)))
        return tuple(map(vibrate_rgb, color))

    def add_player(self, snake_id, position=MAP_CENTER, color=None):
        """ Add a new snake into the game """
        if color is None:
            color = self.randcolor(100)
        self.snakes[snake_id] = Snake(position, color)

    def distance2p(self, p1, p2):
        """ Return distance between two points on a 2d map """
        vec1 = pg.math.Vector2(p1[0], p1[1])
        vec2 = pg.math.Vector2(p2[0], p2[1])
        return vec1.distance_to(vec2)
    
    def kill_snake(self, snake_id):
        """ Kill a snake and turn its body into food """
        if not snake_id in self.snakes:
            return
        
        # Using len(.positions) instead of .length to get actual body length on the map
        tot_val = len(self.snakes[snake_id].positions)
        # Turning its body into food
        while tot_val > 0:
            pos = self.vibrate_pos(random.choice(self.snakes[snake_id].positions))
            if pos in self.food:
                continue
            color = self.vibrate_color(self.snakes[snake_id].color, -10, 40)
            radius = random.uniform(max(0, FOOD_BODY_RADIUS_AVE*3/4), FOOD_BODY_RADIUS_AVE*5/4)
            value = min(tot_val, random.uniform(max(0, FOOD_BODY_VALUE_AVE/2), FOOD_BODY_VALUE_AVE*3/2))
            self.food[pos] = {
                "color": color, 
                "radius": radius, 
                "value": value
            }
            tot_val -= value

        del self.snakes[snake_id]

    def handle_collision(self, snake_id):
        """
        Handle collision between snake head and other objects.
        Return True when snake killed, else return False.
        """
        def is_in_box(box, pos, r=0):
            """ Determin if a point is closer than r to a limit_box """
            return (pos[0]>=box[0]-r and pos[0]<=box[1]+r and pos[1]>=box[2]-r and pos[1]<=box[3]+r)
        
        if not snake_id in self.snakes:
            return True

        ra = self.snakes[snake_id].radius
        head_pos = self.snakes[snake_id].head()
        # Collision with the edge of the map
        if head_pos[0] <= ra or head_pos[1] <= ra or head_pos[0] >= MAP_WIDTH-ra or head_pos[1] >= MAP_HEIGHT-ra:
            self.kill_snake(snake_id)
            return True

        # Collision with other snakes
        for snake in self.snakes.values():
            if snake == self.snakes[snake_id] or not is_in_box(snake.limit_box, head_pos, ra+snake.radius):
                continue
            for p in snake.positions:
                if self.distance2p(head_pos, p) <= ra+snake.radius:
                    self.kill_snake(snake_id)
                    return True

        # "Collision" with food
        f_range = int(ra+FOOD_RADIUS_AVE)
        for x in range(head_pos[0]-f_range, head_pos[0]+f_range):
            for y in range(head_pos[1]-f_range, head_pos[1]+f_range):
                if (x, y) in self.food:
                    self.snakes[snake_id].length += self.food[(x, y)]["value"]
                    del self.food[(x, y)]

        return False

    def update_game(self):
        """ Move the snakes and adjust food on the map. Return the IDs of killed snakes"""
        death_records = []
        self.update_food()
        for snake_id in list(self.snakes):
            if self.handle_collision(snake_id):
                death_records.append(snake_id)
                continue
            self.snakes[snake_id].move()
        return death_records

    def update_player(self, snake_id, direction=None, speed=None):
        """ Update parameters of a snake from user input but do not move the player """
        if not snake_id in self.snakes:
            return False
        if not direction is None:
            self.snakes[snake_id].direction = direction 
        if not speed is None:
            self.snakes[snake_id].speed = speed
        return True

    def update_food(self, amount=FOOD_MIN):
        """ Adjust the amount of food on the map """
        # Not enough food
        while len(self.food) < amount:
            pos = (random.randint(0, MAP_WIDTH), random.randint(0, MAP_HEIGHT))
            if pos in self.food.keys():
                continue
            color = self.randcolor()
            radius = random.uniform(FOOD_RADIUS_AVE*3/4, FOOD_RADIUS_AVE*5/4)
            value = random.uniform(max(0, FOOD_VALUE_AVE/2), FOOD_VALUE_AVE*3/2)
            self.food[pos] = {
                "color": color, 
                "radius": radius, 
                "value": value
            }
        # Too much food (2x)
        #while len(self.food) > amount*2:
            #fpos = random.choice(list(self.food.keys()))
            #del self.food[fpos]
    
    def get_zf(self, snake_id):
        """ Calculate camera zoom factor (zf) based on snake radius """
        if not snake_id in self.snakes:
            return None 
        return math.sqrt(self.snakes[snake_id].radius/SNAKE_RADIUS_MIN)/ZOOM_INDEX
    
    def get_cam_center(self, head_pos, zf):
        """ Calculate the position of the center of the camera on the map """
        x = max(SCREEN_WIDTH*zf/2, min(MAP_WIDTH-(SCREEN_WIDTH*zf/2), head_pos[0]))
        y = max(SCREEN_HEIGHT*zf/2, min(MAP_HEIGHT-(SCREEN_HEIGHT*zf/2), head_pos[1]))
        return (x, y)
    
    def get_position(self, pos, cam_center, zf):
        """ Get screen coordinates based on map coordinates """
        return (round(SCREEN_WIDTH/2-(cam_center[0]-pos[0])/zf), 
                round(SCREEN_HEIGHT/2-(cam_center[1]-pos[1])/zf))
    
    def invert_get_position(self, pos, cam_center, zf):
        """ Get map coordinates based on screen coordinates """
        return (round(cam_center[0]+(pos[0]-SCREEN_WIDTH/2)*zf), 
                round(cam_center[1]+(pos[1]-SCREEN_HEIGHT/2)*zf))

    def render(self, screen, head_pos, zf, *, p_names=True, p_box=False):
        """
        Render the map, the head of the given snake placed at the center.
        Camera zooms out when the snake gets bigger.
        """
        # Get screen distances baded on map distances
        get_distance = lambda d: (d/zf)

        # Decide if a dot is in the screen
        is_in_screen = lambda pos: (pos[0] >= 0 and pos[1] >= 0 and pos[0] <= SCREEN_WIDTH and pos[1] <= SCREEN_HEIGHT)

        ccx, ccy = self.get_cam_center(head_pos, zf)
        # Render food
        for fpos in self.food:
            pos = self.get_position(fpos, (ccx, ccy), zf)
            if is_in_screen(pos):
                pg.draw.circle(screen, self.food[fpos]["color"], pos, self.food[fpos]["radius"], 0)

        # Render snakes
        for s in self.snakes.values():
            pos_v = (-1e5, -1e5) # Last visible position
            # Render limit_box
            if p_box:
                x1, x2, y1, y2 = s.limit_box
                cam_center = (ccx, ccy)
                pg.draw.line(screen, GREEN, self.get_position((x1, y1), cam_center, zf), 
                            self.get_position((x1, y2), cam_center, zf), width=1)
                pg.draw.line(screen, GREEN, self.get_position((x2, y1), cam_center, zf), 
                            self.get_position((x2, y2), cam_center, zf), width=1)
                pg.draw.line(screen, GREEN, self.get_position((x1, y1), cam_center, zf), 
                            self.get_position((x2, y1), cam_center, zf), width=1)
                pg.draw.line(screen, GREEN, self.get_position((x1, y2), cam_center, zf), 
                            self.get_position((x2, y2), cam_center, zf), width=1)
            for i in range(len(s.positions)-1, -1, -1):
                if self.distance2p(s.positions[i], pos_v) >= BODY_INTERVAL*(s.radius/SNAKE_RADIUS_MIN):
                    pos_v = s.positions[i]
                    ps = self.get_position(s.positions[i], (ccx, ccy), zf)
                    ps = self.vibrate_pos(ps, factor=8*(s.speed-SPEED_NORMAL))
                    if is_in_screen(ps):
                        pg.draw.circle(screen, s.color, ps, get_distance(s.radius), 0)
        
        # Print names of the snakes
        if p_names:
            font = pg.font.Font(None, 15)
            for s_id in self.snakes:
                text = font.render(f"{s_id}", True, WHITE)
                screen.blit(text, self.get_position(self.snakes[s_id].positions[-1], (ccx, ccy), zf))

        # Render the edges of the map
        Line_width = 10
        if math.floor(ccx-SCREEN_WIDTH*zf/2) == 0:
            pg.draw.line(screen, RED, (0, 0), (0, SCREEN_HEIGHT-1), width=Line_width)
        if math.floor(ccy-SCREEN_HEIGHT*zf/2) == 0:
            pg.draw.line(screen, RED, (0, 0), (SCREEN_WIDTH-1, 0), width=Line_width)
        if math.ceil(ccx+SCREEN_WIDTH*zf/2) == MAP_WIDTH:
            pg.draw.line(screen, RED, (SCREEN_WIDTH-1, 0), (SCREEN_WIDTH-1, SCREEN_HEIGHT-1), width=Line_width)
        if math.ceil(ccy+SCREEN_HEIGHT*zf/2) == MAP_HEIGHT:
            pg.draw.line(screen, RED, (0, SCREEN_HEIGHT-1), (SCREEN_WIDTH-1, SCREEN_HEIGHT-1), width=Line_width)

    def snake_is_on_screen(self, snake_id, cam_center, zf):
        """ Decide if I can see a snake on my screen """
        # "Snake" box
        x1, x2, y1, y2 = self.snakes[snake_id].limit_box
        # Screen box
        cx1, cy1 = self.invert_get_position((0, 0), cam_center, zf)
        cx2, cy2 = self.invert_get_position((SCREEN_WIDTH, SCREEN_HEIGHT), cam_center, zf)
        # If two boxes overlap return True
        return x2 >= cx1 and y2 >= cy1 and x1 <= cx2 and y1 <= cy2