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

#****************************************************************************
#
#****************************************************************************
"""Both buildings and weapons are considered units since they are launched in the same way. Doodads are also units but are generally treated differently in the game."""
class Unit:
    def __init__(self, id, type, playerID):
        self.id = id
        self.type = type
        self.playerID = playerID    
        self.teamID = 0
        self.dir = 0
        self.owner = None
        self.x = 0
        self.y = 0
        self.speed = (0,0)
        self.rotate = 3
        self.typeset = None
        self.hp = 0
        self.parentID = 0
        self.glow_tether = 1
        self.disabled = False
        self.collecting = False
        self.blasted = False
        self.virused = False
        self.just_virused = False
        self.was_virused = False
        self.was_virused2 = False
        self.check_virus = False
        self.reloading = False

