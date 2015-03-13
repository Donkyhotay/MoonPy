"""Copyright 2009:
    Isaac Carroll, Kevin Clement, Jon Handy, David Carroll, Daniel Carroll

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
"""

import pygame

class HoldButton:
    def __init__(self, client):
        self.client = client
        self.just_released = False

    def rotateright(self):        self.client.rotate_position[self.client.clientID] = self.client.rotate_position[self.client.clientID] + 2
        if (self.client.rotate_position[self.client.clientID] > 360):
            self.client.rotate_position[self.client.clientID] = 1

    def rotateleft(self):
        self.client.rotate_position[self.client.clientID] = self.client.rotate_position[self.client.clientID] - 2
        if (self.client.rotate_position[self.client.clientID] < 1):
            self.client.rotate_position[self.client.clientID] = 360

    def increasepower(self):
        self.client.firepower = self.client.firepower + 1
        if self.client.firepower > 25:
            self.client.firepower = 25
        pygame.time.delay(3)

    def decreasepower(self):
        self.client.firepower = self.client.firepower - 1
        if self.client.firepower < 1:
            self.client.firepower = 1
        pygame.time.delay(3)

    def firing(self):
        if self.client.power_direction == "up":
            self.client.firepower = self.client.firepower + 1
        if self.client.power_direction == "down":
            self.client.firepower = self.client.firepower - 1
        if self.client.firepower == 25:
            self.client.power_direction = "down"
        if self.client.firepower == 1:
            self.client.moonaudio.sound("powerbar.ogg")
            self.client.power_direction = "up"
        pygame.time.delay(20)
