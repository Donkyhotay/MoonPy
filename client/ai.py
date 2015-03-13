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
import sys
from random import *


class AI:
    def __init__(self, client):
        self.client = client
        self.launching_unit = 0
        self.selected_weap = "bomb"
        self.rotation = 360
        self.power = 0
        self.skip = False

    def runbot(self, AIlevel): #this chooses which bot to run, each bot needs to choose a weapon, a place to launch from, a direction, and a power level
        if AIlevel < 1:
            logging.critical("Invalid AI level " + str(AIlevel) + " selected")
            sys.exit(1)
        elif AIlevel == 1:
            self.dumbbot()
        else:
            logging.critical("Invalid AI level " + str(AIlevel) + " selected")
            sys.exit(1)
        return(self.launching_unit, self.selected_weap, self.rotation, self.power, self.skip)

    def dumbbot(self):
        logging.info("Dumbbot is taking a turn...")
        eligiblelaunchers = []
        for unit in self.client.map.unitstore.values():
            if unit.playerID == self.client.playerID[self.client.clientID] and unit.type.id == "hub":
                eligiblelaunchers.append(unit.id)
        chooselauncher = randint(0, (len(eligiblelaunchers) - 1))
        self.launching_unit = eligiblelaunchers[chooselauncher]
        self.power = randint(1, 25)
        self.rotation = randint(1, 360)
        self.skip = False
        if self.client.energy[self.client.clientID] > 6:
            choseweap = randint(0, 18)
        elif self.client.energy[self.client.clientID] > 2:
            choseweap = randint(0, 12)
        else:
            choseweap = randint(0, 6)
        if choseweap == 0:
            self.skip = True
        elif choseweap == 1:
            self.selected_weap = "bomb"
        elif choseweap == 2:
            self.selected_weap = "antiair"
        elif choseweap == 3:
            self.selected_weap = "bridge"
        elif choseweap == 4:
            self.selected_weap = "tower"
        elif choseweap == 5:
            self.selected_weap = "repair"
        elif choseweap == 6:
            self.selected_weap = "cluster"
        elif choseweap == 7:
            self.selected_weap = "recall"
        elif choseweap == 8:
            self.selected_weap = "spike"
        elif choseweap == 9:
            #self.selected_weap = "ballon"
            self.selected_weap = "bomb" #balloons are disabled
        elif choseweap == 10:
            self.selected_weap = "emp"
        elif choseweap == 11:
            self.selected_weap = "missile"
        elif choseweap == 12:
            self.selected_weap = "mines"
        elif choseweap == 13:
            self.selected_weap = "crawler"
        elif choseweap == 14:
            self.selected_weap = "collector"
        elif choseweap == 15:
            self.selected_weap = "hub"
        elif choseweap == 16:
            self.selected_weap = "offense"
        elif choseweap == 17:
            self.selected_weap = "shield"
        elif choseweap == 18:
            self.selected_weap = "virus"
