"""
Including Snake class.
Github: https://github.com/neilc24/slither24
"""

import math

from config import *

class Snake:
    def __init__ (self, pos, color):
        self.positions = [pos]
        self.direction = DIRECTION_INIT # Direction from user
        self.angle = DIRECTION_INIT # Actual direction
        self.speed = SPEED_NORMAL
        self.length = LENGTH_MIN
        self.color = color
        self.radius = SNAKE_RADIUS_MIN

    def __str__ (self):
        return f"<Head={self.head()}, L={self.length:.0f}, Direction={self.angle:.1f}, R={self.radius:.2f}>"
    
    def head(self):
        """ Return the position of the head """
        return self.positions[-1]

    def update_radius(self):
        """ Update radius based on the length """
        self.radius = SNAKE_RADIUS_MIN*math.pow(self.length/LENGTH_MIN, 0.125) * math.log(self.length, LENGTH_MIN)

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
        
        self.direction = aformat(self.direction)
        self.angle = aformat(self.angle)

        if diff_angles(self.angle, self.direction) > ANGLE_MAX:
            if diff_angles(self.angle+ANGLE_MAX, self.direction) < diff_angles(self.angle-ANGLE_MAX, self.direction):
                self.angle = aformat(self.angle+ANGLE_MAX)
            else:
                self.angle = aformat(self.angle-ANGLE_MAX)
        else:
            self.angle = self.direction
        
        if self.speed > SPEED_NORMAL and self.length - SPEEDUP_COST >= LENGTH_MIN:
            self.length -= SPEEDUP_COST
        else:
            self.speed = SPEED_NORMAL
        
        p = list(self.head())
        p[0] += round(math.cos(math.radians(self.angle)) * self.speed)
        p[1] -= round(math.sin(math.radians(self.angle)) * self.speed) # In pygame up and down are reversed
        self.positions.append(tuple(p))
        while(len(self.positions) > self.length):
            self.positions = self.positions[1:]

        self.update_radius()