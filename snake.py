"""
snake.py
Github: https://github.com/neilc24/slither24
"""

import math

from config import *

class Snake:
    def __init__ (self, head_pos, color, *, 
                  direction=DIRECTION_INIT, speed=SPEED_NORMAL, 
                  length=LENGTH_MIN, radius=SNAKE_RADIUS_MIN):
        self.positions = [head_pos]
        self.direction = direction # Direction from user
        self.angle = self.direction # Actual direction
        self.speed = speed
        self.length = length
        self.color = color
        self.radius = radius
        # The whole body must be in the rectangle(left, right, up, down)
        # (For the convenience of collision detection)
        self.limit_box = (self.head()[0], self.head()[0], self.head()[1], self.head()[1])

    def __str__ (self):
        return f"<Snake Head={self.head()}, Direction={self.angle:.1f}, Length={self.length:.0f}>"
    
    def head(self):
        """ Return the position of the head """
        return self.positions[-1]

    def update_radius(self):
        """ Update self.radius based on self.length """
        self.radius = SNAKE_RADIUS_MIN*math.pow(self.length/LENGTH_MIN, 0.125) * math.log(self.length, LENGTH_MIN)
        return self.radius

    def update_limit_box(self):
        """ Update self.limit_box based on self.positions """
        left, right = min(x for x, y in self.positions), max(x for x, y in self.positions)
        up, down = min(y for x, y in self.positions), max(y for x, y in self.positions)
        self.limit_box = (left, right, up, down)
        return self.limit_box

    def move(self):
        """ Move the snake forward """
        def aformat(a):
            """ Formatting an angle in degrees """
            a = a % 360
            if a < 0:
                a += 360
            return a
        
        def diff_angles(a, b):
            """ Calculate the smallest difference between 2 angles """
            return min(abs(aformat(a)-aformat(b)), 360-abs(aformat(a)-aformat(b)))
        
        # Calculate self.angle
        self.direction, self.angle = aformat(self.direction), aformat(self.angle)
        if diff_angles(self.angle, self.direction) > ANGLE_MAX:
            if diff_angles(self.angle+ANGLE_MAX, self.direction) < diff_angles(self.angle-ANGLE_MAX, self.direction):
                self.angle = aformat(self.angle+ANGLE_MAX)
            else:
                self.angle = aformat(self.angle-ANGLE_MAX)
        else:
            self.angle = self.direction
        
        # self.speed and self.length related calculation
        if self.speed > SPEED_NORMAL and self.length - SPEEDUP_COST >= LENGTH_MIN:
            self.length -= SPEEDUP_COST
        else:
            self.speed = SPEED_NORMAL
        
        # Move the snake forward
        p = list(self.head())
        p[0] += round(math.cos(math.radians(self.angle)) * self.speed)
        p[1] -= round(math.sin(math.radians(self.angle)) * self.speed) # In pygame up and down are reversed
        self.positions.append(tuple(p))
        while(len(self.positions) > self.length):
            self.positions = self.positions[1:]

        self.update_radius()
        self.update_limit_box()