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

import logging
from random import *
from common.map import *

#****************************************************************************
#create a new random map
#****************************************************************************
class MapGen:
    def __init__(self, map, ruleset):
        self.map = map
        self.ruleset = ruleset
        self.waterlevel = 6
        self.maxheight = 22 

        logging.info("Generating a random new map")
        self.generate_heights()


#****************************************************************************
#
#****************************************************************************
    def generate_heights(self):
        heightmap_a = {}
        heightmap_b = {}

        # Randomly generate a heightmap
        for x in range(self.map.xsize):
            for y in range(self.map.ysize):
                heightmap_a[x,y] = randint(0, self.maxheight)

        # Gaussian blur operation on heightmap
        # with a 3x3 convolution matrix.
        for i in range(4):
            for x in range(self.map.xsize):
                for y in range(self.map.ysize):
                    if (x == 0 or y == 0 or x+1== self.map.xsize or y+1 == self.map.ysize):
                        heightmap_b[x,y] = 0
                        continue 
                    heightmap_b[x,y] = (heightmap_a[x-1,y] + heightmap_a[x+1,y] + heightmap_a[x,y-1] + heightmap_a[x,y+1] + heightmap_a[x+1,y+1] + heightmap_a[x-1,y-1] + heightmap_a[x-1,y+1] + heightmap_a[x+1,y-1]) / 8
            heightmap_a = heightmap_b    

        # Subtract heightmap with waterlevel.
        for x in range(self.map.xsize):
            for y in range(self.map.ysize):
                if (heightmap_a[x,y] < self.waterlevel):
                    heightmap_a[x,y] = self.waterlevel
                heightmap_a[x,y] -= self.waterlevel

        # Create terrain types oceans and plains
        for x in range(self.map.xsize):
            for y in range(self.map.ysize):
                tile = self.map.get_tile((x, y))
                if (int(heightmap_a[x,y]) == 0):
                    tile.type = self.ruleset.get_terrain_type("water")
                elif (int(heightmap_a[x, y])) == 4:
                    tile.type = self.ruleset.get_terrain_type("rocks")
                elif (int(heightmap_a[x, y])) == 3:
                    if randint(0, 250) == 5:
                        tile.type = self.ruleset.get_terrain_type("energy")
                    else:
                        tile.type = self.ruleset.get_terrain_type("grass")
                else:
                    tile.type = self.ruleset.get_terrain_type("grass")
