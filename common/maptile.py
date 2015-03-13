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

#****************************************************************************
#
#****************************************************************************
class MapTile:
    def __init__(self, type, x, y):
        self.x = x
        self.y = y
        self.type = type  

#****************************************************************************
# Test for equality with tile. Must be implemented for pathfinding
#****************************************************************************
    def __eq__(self, tile):
        if tile == None: 
            return 0
      
        if tile.x == self.x and tile.y == self.y:
            return 1
        else:
            return 0

