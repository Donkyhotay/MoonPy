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

import os, sys
import pygame
import time
import logging
from pygame.locals import *

import tileset

#****************************************************************************
# The Minimap is a _mini_ map. 
#****************************************************************************
class Minimap:

    def __init__(self, clientstate, x, y, width, height):
        self.client = clientstate
        self.width = width
        self.height = height
        self.x = x
        self.y = y

        self.count = 0

#****************************************************************************
# Updates the minimap. 
#****************************************************************************
    def update(self):

        self.minimap_surface = pygame.Surface((self.client.map.ysize, self.client.map.xsize))

        self.client.updated_map = False

        for y in range(self.client.map.ysize):
            for x in range(self.client.map.xsize):
                tile = self.client.map.get_tile((x, y))
                if (tile.type.id == "water"):
                    color = (12, 42, 130)
                elif (tile.type.id == "rocks"):
                    color = (200, 200, 200)
                elif (tile.type.id == "energy"):
                    color = (255, 0, 255)
                else: #regular ground
                    color = (25, 175, 75)    
                self.minimap_surface.set_at((x, y), color)

        for unit in self.client.map.get_unit_list():
            if unit.typeset != "doodad":
                x, y = self.client.map.get_unit_pos(unit)
                if unit.playerID == self.client.playerID[self.client.clientID]:
                    color = (10, 255, 10)
                elif unit.teamID == self.client.teamID[self.client.clientID]:
                    color = (10, 10, 255)
                else:
                    color = (255, 10, 10)
                self.minimap_surface.set_at((x, y), color)
                if unit.typeset == "build": #this takes into account most units are 4 times the size of a standard tile
                    self.minimap_surface.set_at(((x + 1), y), color)
                    self.minimap_surface.set_at((x, (y + 1)), color)
                    self.minimap_surface.set_at(((x + 1), (y + 1)), color)
        self.minimap_surface = pygame.transform.scale(self.minimap_surface, (100, 100))


#****************************************************************************
# Draws the entire minimap to the screen.
#****************************************************************************
    def draw(self):
        self.count += 1
        # FIXME: This updates every 60th frame. Should only update when map is updated for better efficiency
        if self.client.updated_map == True:
            self.update()
        if not self.minimap_surface:
            self.update()
        self.client.screen.blit(self.minimap_surface, (self.x, self.y))


#****************************************************************************
# Handles mouse click events.
#****************************************************************************
    def handle_mouse_click(self, pos):
        (x, y) = pos
        #map_x = x - self.x
        #map_y = y - self.y
        map_x = (x - self.x) * self.client.map.xsize / 100;
        map_y = (y - self.y) * self.client.map.ysize / 100;
        self.client.mapview.center_view_on_tile((map_x, map_y))
        self.update()

