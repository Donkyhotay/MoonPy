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
from twisted.internet import task, reactor
from twisted.cred.portal import Portal
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from twisted.spread import pb
from twisted.cred.portal import IRealm

from common.map import * 
from common.game import * 
from common.mapgen import *
from common.settings import *
from connectionhandler import *


#****************************************************************************
#
#****************************************************************************
class ServerState:
    def __init__(self):
        self.settings = GameSettings()
        self.game = None 
        self.currentplayer = 1
        self.skippedplayers = []
        self.deadplayers = []
        self.playerIDs = []
        self.teams = []
        self.teams.append(0) #these can *not* be empty or next player/teams will never be found
        self.skippedplayers.append(0) 
        self.deadplayers.append(0)
        self.interrupted_tether = False
        self.waitingclients = 0
        self.runningserver = False
        self.doubletether = False
        self.takingturn = False
        self.endgame = False
        self.roundplayer = 1
        self.mapX = 90
        self.mapY = 90
        self.game_type = "classic"
 
#****************************************************************************
#Starts a new game, loads the map, adds starting hubs
#****************************************************************************
    def setup_new_game(self):

        if not self.game:
            self.connections.remote_all("resize_map", self.mapX, self.mapY)
            self.map = Map(self, self.mapX, self.mapY)
            self.game = Game(self.map)

            MapGen(self.map, self.game)

            for player in range(1, (self.max_players() + 1)):
                unplaced = True
                while unplaced: #make certain starting hub is placed on grass
                    x = randint(5, (self.map.xsize - 5))
                    y = randint(5, (self.map.xsize - 5))
                    (tile1, tile2, tile3, tile4, tile5, tile6, tile7, tile8, tile9) = self.game.find_connecting_points(x, y)
                    tile1 = self.map.get_tile(tile1)
                    tile2 = self.map.get_tile(tile2)
                    tile3 = self.map.get_tile(tile3)
                    tile4 = self.map.get_tile(tile4)
                    tile5 = self.map.get_tile(tile5)
                    tile6 = self.map.get_tile(tile6)
                    tile7 = self.map.get_tile(tile7)
                    tile8 = self.map.get_tile(tile8)
                    tile9 = self.map.get_tile(tile9)
                    if tile1.type == self.game.get_terrain_type("grass") and tile2.type == self.game.get_terrain_type("grass") and tile3.type == self.game.get_terrain_type("grass") and tile4.type == self.game.get_terrain_type("grass") and tile5.type == self.game.get_terrain_type("grass") and tile6.type == self.game.get_terrain_type("grass") and tile7.type == self.game.get_terrain_type("grass") and tile8.type == self.game.get_terrain_type("grass") and tile9.type == self.game.get_terrain_type("grass"):
                        unplaced = False
                self.game.create_unit('hub', (x, y), (player), 0, False, 360, self.teams[(player)])

            #Initialize main loop callback.
            self.loop = task.LoopingCall(self.mainloop)
            self.loop.start(1.0)


#****************************************************************************
# This method is called every second.
#****************************************************************************
    def mainloop(self):
        self.connections.remote_all('network_sync')


#****************************************************************************
#find and remove all units without any HP remaining
#****************************************************************************
    def process_death(self):
        #This function searches for units without any HP remaining, removes them from the game, then sets the HP of any dependent units connected to them to 0. This function then repeats the process until all dependent units are found and removed
        logging.debug("processing death")
        notclear = True
        bridgedeath = False
        while notclear:
            notclear = False
            for unit in self.map.unitstore.values():
                unit.check_virus = False
                for unblast in self.map.unitstore.values():
                    unblast.blasted = False
                if unit.typeset == "tether" and unit.hp > 0: #tethers heal between turns so they never die except by death of parent
                    unit.hp = 1000
                if (unit.hp < 1 and unit.typeset != "doodad"):
                    notclear = True
                    radius = self.game.get_unit_radius(unit.type.id) + 1
                    if unit.type.id == "bridge":
                        bridgedeath = True
                    if unit.type.id == "mines" and unit.disabled == False:
                        power = self.game.get_unit_power(unit.type.id)
                        endX = unit.x
                        endY = unit.y
                        for find_target in range(0, radius):
                            spinner = 0
                            while spinner < 360:
                                if find_target == 0:
                                    endX = unit.x
                                    endY = unit.y
                                    spinner = 355
                                else:
                                    endX = find_target * math.cos(spinner / 180.0 * math.pi)
                                    endY = find_target * math.sin(spinner / 180.0 * math.pi)
                                    endX = round(endX, 0)
                                    endY = round(endY, 0)
                                    endX = int(endX) + unit.x
                                    endY = int(endY) + unit.y
                                logging.debug("Radius, Spinner = %s, %s" % (find_target, spinner))
                                for target in self.map.unitstore.values():
                                    logging.debug("comparing possible targets: %s, %s - %s, %s" % (endX, endY, target.x, target.y))
                                    if target.x == endX and target.y == endY and target.typeset != "doodad" and target.blasted == False:
                                        target.hp = target.hp - power #unit is caught in explosion and damaged
                                        target.blasted = True
                                    if target.x == unit.x and target.y == unit.y and target.typeset != "doodad" and target.blasted == False:
                                        target.hp = target.hp - power #unit is caught in explosion and damaged
                                        target.blasted = True
                                spinner = spinner + 5
                    if unit.type.id == "crawler" and unit.disabled == False:
                        power = self.game.get_unit_power(unit.type.id)
                        endX = unit.x
                        endY = unit.y
                        for find_target in range(0, radius):
                            spinner = 0
                            while spinner < 360:
                                if find_target == 0:
                                    endX = unit.x
                                    endY = unit.y
                                    spinner = 355
                                else:
                                    endX = find_target * math.cos(spinner / 180.0 * math.pi)
                                    endY = find_target * math.sin(spinner / 180.0 * math.pi)
                                    endX = round(endX, 0)
                                    endY = round(endY, 0)
                                    endX = int(endX) + unit.x
                                    endY = int(endY) + unit.y
                                logging.debug("Radius, Spinner = %s, %s" % (find_target, spinner))
                                for target in self.map.unitstore.values():
                                    logging.debug("comparing possible targets: %s, %s - %s, %s" % (endX, endY, target.x, target.y))
                                    if target.x == endX and target.y == endY and target.typeset != "doodad" and target.blasted == False:
                                        target.hp = target.hp - power #unit is caught in explosion and damaged
                                        target.blasted = True
                                    if target.x == unit.x and target.y == unit.y and target.typeset != "doodad" and target.blasted == False:
                                        target.hp = target.hp - power #unit is caught in explosion and damaged
                                        target.blasted = True
                                spinner = spinner + 5
                    if unit.type.id == "collector" and unit.disabled == False:
                        logging.info("collector went critical")
                        endX = unit.x
                        endY = unit.y
                        for find_target in range(0, radius):
                            spinner = 0
                            while spinner < 360:
                                if find_target == 0:
                                    endX = unit.x
                                    endY = unit.y
                                    spinner = 355
                                else:
                                    endX = find_target * math.cos(spinner / 180.0 * math.pi)
                                    endY = find_target * math.sin(spinner / 180.0 * math.pi)
                                    endX = round(endX, 0)
                                    endY = round(endY, 0)
                                    endX = int(endX) + unit.x
                                    endY = int(endY) + unit.y
                                logging.debug("Radius, Spinner = %s, %s" % (find_target, spinner))
                                for target in self.map.unitstore.values():
                                    logging.debug("comparing possible targets: %s, %s - %s, %s" % (endX, endY, target.x, target.y))
                                    if target.x == endX and target.y == endY and target.typeset != "doodad" and target.blasted == False:
                                        logging.info("unit got caught in nuke")
                                        target.hp = target.hp - 5 #unit is caught in explosion and damaged
                                        target.blasted = True
                                    if target.x == unit.x and target.y == unit.y and target.typeset != "doodad" and target.blasted == False:
                                        target.hp = target.hp - power #unit is caught in explosion and damaged
                                        target.blasted = True
                                spinner = spinner + 5
                    self.connections.remote_all('kill_unit', unit.x, unit.y, unit.typeset, unit.playerID, unit.type.id, unit.disabled)
                    self.game.remove_unit(unit)
                    for unit2 in self.map.unitstore.values(): 
                        if unit2.parentID == unit.id:
                            unit2.hp = 0
        if bridgedeath == True:
            self.handle_water()

#****************************************************************************
#find and move viruses
#****************************************************************************
    def process_virus(self):
        logging.debug("processing virus")
        logging.debug("new virus process")
        for unit in self.map.unitstore.values():
            unit.check_virus = True
            if unit.was_virused == True:
                if unit.was_virused2 == True:
                    unit.was_virused = False
                else:
                    unit.was_virused = False
            if unit.virused == True and unit.typeset != "build": #remove viruses from non-buildings
                unit.virused = False
                unit.just_virused = False
                logging.debug("removed virus from non-building " + str(unit.id))
                logging.debug("listed typeset here is " + str(unit.typeset))

            elif unit.virused == True and unit.typeset == "build": #virus is spreading
                if unit.just_virused == True: #don't spread if just virused
                    unit.just_virused = False
                    logging.debug("unit " + str(unit.id) + " remains virused but is not just-virused")
                else: #virus will spread
                    unit.virused = False
                    unit.was_virused = True
                    logging.debug("virus has expired from unit " + str(unit.id))
                    if unit.hp > 1:
                        unit.hp = unit.hp - 1
                        logging.debug("virus damaged unit " + str(unit.id))
                    for find_tethered in self.map.unitstore.values():
                        if find_tethered.was_virused == False and find_tethered.was_virused2 == False and (find_tethered.id == unit.parentID or find_tethered.parentID == unit.id) and find_tethered.typeset == "build":
                            logging.info("virus has spread to unit %s" % find_tethered.id)
                            logging.debug("virus has spread to unit " + str(find_tethered.id))
                            find_tethered.virused = True
                            if find_tethered.id > unit.id:
                                unit.was_virused2 = True
                            if find_tethered.check_virus == False:
                                find_tethered.just_virused = True
                            else:
                                find_tethered.just_virused = False
        self.handle_water()

#****************************************************************************
#handle bridges, units in water and destruction
#****************************************************************************
    def handle_water(self): #todo: convert all death by water to this function
        logging.debug("handling water")
        for unit in self.map.unitstore.values():
            tile1 = self.map.get_tile((unit.x, unit.y))
            tile2 = self.map.get_tile(((unit.x + 1), unit.y))
            tile3 = self.map.get_tile((unit.x, (unit.y + 1)))
            tile4 = self.map.get_tile(((unit.x + 1), (unit.y + 1)))
            tile5 = self.map.get_tile(((unit.x - 1), (unit.y - 1)))
            tile6 = self.map.get_tile(((unit.x - 1), unit.y))
            tile7 = self.map.get_tile((unit.x, (unit.y - 1)))
            tile8 = self.map.get_tile(((unit.x + 1), (unit.y - 1)))
            tile9 = self.map.get_tile(((unit.x - 1), (unit.y + 1)))

            if unit.type.id == "bridge":
                if tile1.type != self.game.get_terrain_type("water") and tile2.type != self.game.get_terrain_type("water") and tile3.type != self.game.get_terrain_type("water") and tile4.type != self.game.get_terrain_type("water") and tile5.type != self.game.get_terrain_type("water") and tile6.type != self.game.get_terrain_type("water") and tile7.type != self.game.get_terrain_type("water") and tile8.type != self.game.get_terrain_type("water") and tile9.type != self.game.get_terrain_type("water"):
                    unit.hp = 0 #killing bridges that don't land on water

            elif unit.typeset == "build":
                if tile1.type == self.game.get_terrain_type("water") or tile2.type == self.game.get_terrain_type("water") or tile3.type == self.game.get_terrain_type("water") or tile4.type == self.game.get_terrain_type("water") or tile5.type == self.game.get_terrain_type("water") or tile6.type == self.game.get_terrain_type("water") or tile7.type == self.game.get_terrain_type("water") or tile8.type == self.game.get_terrain_type("water") or tile9.type == self.game.get_terrain_type("water"):
                    gosplash = True
                    for unit2 in self.map.unitstore.values():
                        (crosscheck1, crosscheck2, crosscheck3, crosscheck4, crosscheck5, crosscheck6, crosscheck7, crosscheck8, crosscheck9) = self.game.find_connecting_points(unit2.x, unit2.y)
                        if  unit2.type.id == "bridge" and (crosscheck1 == (unit.x, unit.y) or crosscheck2 == (unit.x, unit.y) or crosscheck3 == (unit.x, unit.y) or crosscheck4 == (unit.x, unit.y) or crosscheck5 == (unit.x, unit.y) or crosscheck6 == (unit.x, unit.y) or crosscheck7 == (unit.x, unit.y) or crosscheck8 == (unit.x, unit.y) or crosscheck9 == (unit.x, unit.y)):
                            gosplash = False
                    if gosplash == True:
                        unit.hp = 0
                        self.connections.remote_all("splash")
                        logging.info("building went splash")

            elif unit.typeset == "tether":
                if tile1.type == self.game.get_terrain_type("water"):
                    gosplash = True
                    for unit2 in self.map.unitstore.values():
                        (crosscheck1, crosscheck2, crosscheck3, crosscheck4, crosscheck5, crosscheck6, crosscheck7, crosscheck8, crosscheck9) = self.game.find_connecting_points(unit2.x, unit2.y)
                        logging.debug("tether is at location " + str(unit.x) + ", " + str(unit.y))
                        logging.debug("comparing unit.type " + str(unit2.type.id))
                        logging.debug("comparing all unit locations %s %s %s %s %s %s %s %s %s" % (crosscheck1, crosscheck2, crosscheck3, crosscheck4, crosscheck5, crosscheck6, crosscheck7, crosscheck8, crosscheck9))
                        if  unit2.type.id == "bridge" and  (crosscheck1 == (unit.x, unit.y) or crosscheck2 == (unit.x, unit.y) or crosscheck3 == (unit.x, unit.y) or crosscheck4 == (unit.x, unit.y) or crosscheck5 == (unit.x, unit.y) or crosscheck6 == (unit.x, unit.y) or crosscheck7 == (unit.x, unit.y) or crosscheck8 == (unit.x, unit.y) or crosscheck9 == (unit.x, unit.y)):
                            gosplash = False
                    if gosplash == True:
                        logging.info("splashing a tether %s" % str(unit.id))
                        (target1, target2) = self.game.find_tether_ends(unit)
                        logging.debug("Destroying %s as end of splashed tether" % target1)
                        for target in self.map.unitstore.values():
                            if target.id == target1:
                                target.hp = 0
                                self.connections.remote_all("splash")
                                logging.info("finished splashing")
        self.process_death()

#****************************************************************************
#detonate all crawlers/mines that are too close to something
#****************************************************************************
    def detonate_waiters(self):
        logging.debug("detonating waiters")
        for unit in self.map.unitstore.values():
            blasted = False
            if unit.type.id == "mines":
                radius = self.game.get_defense_radius(unit.type.id)
                endX = unit.x
                endY = unit.y
                for find_target in range(1, radius):
                    spinner = 0
                    while spinner < 360:
                        endX = find_target * math.cos(spinner / 180.0 * math.pi)
                        endY = find_target * math.sin(spinner / 180.0 * math.pi)
                        endX = round(endX, 0)
                        endY = round(endY, 0)
                        endX = int(endX) + unit.x
                        endY = int(endY) + unit.y
                        for target in self.map.unitstore.values():
                            logging.debug("comparing possible targets: %s, %s - %s, %s" % (endX, endY, target.x, target.y))
                            if target.x == endX and target.y == endY and target.playerID != unit.playerID and target.typeset != "doodad":
                                unit.hp = 0 #target detonates, damage is incurred while processing death
                        spinner = spinner + 5

            elif unit.type.id == "crawler":
                radius = self.game.get_defense_radius(unit.type.id) #note this is different then the explosive radius!
                endX = unit.x
                endY = unit.y
                for find_target in range(1, radius):
                    spinner = 0
                    while spinner < 360:
                        endX = find_target * math.cos(spinner / 180.0 * math.pi)
                        endY = find_target * math.sin(spinner / 180.0 * math.pi)
                        endX = round(endX, 0)
                        endY = round(endY, 0)
                        endX = int(endX) + unit.x
                        endY = int(endY) + unit.y
                        for target in self.map.unitstore.values():
                            if target.x == endX and target.y == endY and target.playerID != unit.playerID and target.typeset != "doodad":
                                unit.hp = 0 #target detonates, damage is incurred while processing death
                        spinner = spinner + 5
        self.process_virus()


#****************************************************************************
#Move all crawlers at the end of the round
#****************************************************************************
    def move_crawlers(self):
        logging.debug("moving crawlers")
        for unit in self.map.unitstore.values(): #note, in OMBC crawlers move about half a power bar in length
            if unit.type.id == "crawler" and unit.disabled == False:
                start_tile = self.map.get_tile_from_unit(unit)
                undetonated = True
                for find_target in range(1, 15):
                    if undetonated == True:
                        temp_rotation = unit.dir - 90 #following is to adjust for difference between degrees and radians
                        if temp_rotation < 1:
                            temp_rotation = unit.dir + 270
                        endX = find_target * math.cos(temp_rotation / 180.0 * math.pi)
                        endY = find_target * math.sin(temp_rotation / 180.0 * math.pi)
                        endX = round(endX, 0)
                        endY = round(endY, 0)
                        endX = int(endX) + start_tile.x
                        endY = int(endY) + start_tile.y
                        for find_enemy in range(1, self.game.get_defense_radius(unit.type.id)): #search for enemies while moving
                            spinner = 0
                            while spinner < 360:
                                targetX = find_enemy * math.cos(spinner / 180.0 * math.pi)
                                targetY = find_enemy * math.sin(spinner / 180.0 * math.pi)
                                targetX = round(targetX, 0)
                                targetY = round(targetY, 0)
                                targetX = int(targetX) + endX
                                targetY = int(targetY) + endY
                                for target in self.map.unitstore.values():
                                    if target.x == targetX and target.y == targetY and target.playerID != unit.playerID and target.typeset != "doodad":
                                        unit.hp = 0 #target detonates, damage is incurred while processing death
                                        undetonated = False
                                spinner = spinner + 5
                unit.x = endX
                unit.y = endY


#****************************************************************************
#Determine where a shot lands
#****************************************************************************
    def find_trajectory(self, parentID, rotation, power, child, player, clientID):
        playerID = player.playerID[clientID]
        logging.info("player " + str(playerID) + " launched a " + child)
        unit = self.map.get_unit_from_id(parentID)
        start_tile = self.map.get_tile_from_unit(unit)
        endX = start_tile.x #todo: can this be safely removed?
        endY = start_tile.y
        self.interrupted_tether = False
        self.doubletether = False
        power = power + 6 #launching has minimal range, if modifying to forget to change animation distance (in networkclient.py) and split trajectory to compensate
        collecting = False
        for find_target in range(1, power):
            temp_rotation = self.game.deg2rad(rotation)
            endX = find_target * math.cos(temp_rotation / 180.0 * math.pi)
            endY = find_target * math.sin(temp_rotation / 180.0 * math.pi)
            endX = round(endX, 0)
            endY = round(endY, 0)
            endX = int(endX) + start_tile.x
            endY = int(endY) + start_tile.y

            #code for looping the map edges
            if endX < 0:
                endX = self.map.xsize + endX
            if endX > self.map.xsize - 1:
                endX = endX - (self.map.xsize - 1)
            if endY < 0:
                endY = self.map.ysize + endY
            if endY > self.map.ysize - 1:
                endY = endY - (self.map.ysize - 1)

            #determine if shot is intercepted by either an AA or shield
            for lookD in self.map.unitstore.values():
                if lookD.playerID != playerID and (lookD.type.id == "shield" or lookD.type.id == "antiair") and lookD.disabled == False and lookD.virused == False and lookD.reloading == False:
                    radius = self.game.get_defense_radius(lookD.type.id)
                    searchX = lookD.x
                    searchY = lookD.y
                    for find_intercept in range(1, radius):
                        spinner = 0
                        while spinner < 360:
                            searchX = find_intercept * math.cos(spinner / 180.0 * math.pi)
                            searchY = find_intercept * math.sin(spinner / 180.0 * math.pi)
                            searchX = round(searchX, 0)
                            searchY = round(searchY, 0)
                            searchX = int(searchX) + lookD.x
                            searchY = int(searchY) + lookD.y
                            if searchX == endX and searchY == endY:
                                spinner = 360
                                self.interrupted_tether = True
                                self.connections.remote_all("triggered_defense", lookD.x, lookD.y, endX, endY, 1)
                                if lookD.type.id == "antiair":
                                    lookD.reloading = True
                                    player.Ireloading[clientID].append(lookD.id)
                                    player.reload[clientID] = True
                                return (start_tile.x, start_tile.y, endX, endY, collecting)
                            else:
                                spinner = spinner + 5

            #handle missile lockons
            if child == "missile":
                radius = 6
                searchX = endX
                searchY = endY
                for radar in range(1, radius):
                    spinner = 0
                    while spinner < 360:
                        searchX = radar * math.cos(spinner / 180.0 * math.pi)
                        searchY = radar * math.sin(spinner / 180.0 * math.pi)
                        searchX = round(searchX, 0)
                        searchY = round(searchY, 0)
                        searchX = int(searchX) + endX
                        searchY = int(searchY) + endY
                        for target in self.map.unitstore.values():
                            if target.playerID != playerID and searchX == target.x and searchY == target.y and target.typeset == "build":
                                #activate missile engines and change course!
                                temp_rotation = spinner
                                for engines in range(1, radar):
                                    endX = engines * math.cos(temp_rotation / 180.0 * math.pi)
                                    endY = engines * math.sin(temp_rotation / 180.0 * math.pi)
                                    endX = round(endX, 0)
                                    endY = round(endY, 0)
                                    endX = int(endX) + start_tile.x
                                    endY = int(endY) + start_tile.y

                                    #code for looping the map edges
                                    if endX < 0:
                                        endX = self.map.xsize + endX
                                    if endX > self.map.xsize - 1:
                                        endX = endX - (self.map.xsize - 1)
                                    if endY < 0:
                                        endY = self.map.ysize + endY
                                    if endY > self.map.ysize - 1:
                                        endY = endY - (self.map.ysize - 1)

                                    #determine if missile is intercepted by either an AA or shield while engines are on
                                    for lookD in self.map.unitstore.values():
                                        if lookD.playerID != playerID and (lookD.type.id == "shield" or lookD.type.id == "antiair") and lookD.disabled == False and lookD.virused == False and lookD.reloading == False:
                                            radius = self.game.get_defense_radius(lookD.type.id)
                                            searchX = lookD.x
                                            searchY = lookD.y
                                            for find_intercept in range(1, radius):
                                                spinner = 0
                                                while spinner < 360:
                                                    searchX = find_intercept * math.cos(spinner / 180.0 * math.pi)
                                                    searchY = find_intercept * math.sin(spinner / 180.0 * math.pi)
                                                    searchX = round(searchX, 0)
                                                    searchY = round(searchY, 0)
                                                    searchX = int(searchX) + lookD.x
                                                    searchY = int(searchY) + lookD.y
                                                    if searchX == endX and searchY == endY:
                                                        spinner = 360
                                                        self.interrupted_tether = True
                                                        self.connections.remote_all("triggered_defense", lookD.x, lookD.y, endX, endY, 1)
                                                        if lookD.type.id == "antiair":
                                                            lookD.reloading = True
                                                            player.Ireloading[clientID].append(lookD.id)
                                                            player.reload[clientID] = True
                                                        return (start_tile.x, start_tile.y, endX, endY, collecting)
                                                    else:
                                                        spinner = spinner + 5
                                logging.debug("missile homed on target")
                                return (start_tile.x, start_tile.y, target.x, target.y, False)
                            else:
                                spinner = spinner + 5

            #placing tethers if applicable
            if self.game.check_tether(child) == True: #if launched unit has tethers, then place tethers
                retether = False
                for target in self.map.unitstore.values():
                    tile = self.map.get_tile((endX, endY))
                    if (target.x == endX and target.y == endY): #determine if tether crosses another unit/tether
                        if (target.typeset != "doodad") and (target.parentID != parentID):
                            if target.parentID != self.game.unit_counter + 1: #prevents tether from 'crossing' itself due to rounding
                                logging.info("You crossed a tether at step %r" % find_target)
                                self.interrupted_tether = True
                                return (start_tile.x, start_tile.y, endX, endY, collecting)
                            else:
                                logging.info("tether landed on itself")
                                retether = True
                #tether didn't land on anything, ready to place tether! The following is to prevent spaces around the launching hub
                testX = str(endX)
                testY = str(endY)
                if find_target > 1 and find_target < (power - 2) and retether == False:
                    chain_parent = self.game.unit_counter + 2 #tethers have 'reversed' parents
                    self.game.create_unit("tether", (endX, endY), playerID, chain_parent, False, 0, self.teams[playerID])
                    logging.debug("added tether at " + testX + ", " + testY)

        #determine if building landed on rocks or energy pool
        if self.game.get_unit_typeset(child) == "build":
            if self.game.check_tether(child) == True: #previous was for tether itself, this is for the actual building as compared to the individual tethers placed above
                for target in self.map.unitstore.values():
                    tile = self.map.get_tile((endX, endY))
                    if (target.x == endX and target.y == endY): #determine if tether crosses another unit/tether
                        if (target.typeset != "doodad") and (target.parentID != parentID):
                            if target.parentID != self.game.unit_counter + 1: #prevents building from landing on it's own tether
                                logging.info("You crossed a tether at step %r" % find_target)
                                self.interrupted_tether = True
                                return (start_tile.x, start_tile.y, endX, endY, collecting)
                            else:
                                self.doubletether = True #doesn't place 'doubled' tethers due to rounding
                                logging.debug("Building landed on it's own tether")

            tile = self.map.get_tile((endX, endY))
            if tile.type == self.game.get_terrain_type("rocks"):
                self.interrupted_tether = True                
                self.connections.remote_all("hit_rock")
            elif tile.type == self.game.get_terrain_type("energy") and child == "collector":
                collecting = True

            tile = self.map.get_tile((endX + 1, endY))
            if tile.type == self.game.get_terrain_type("rocks"):
                self.interrupted_tether = True               
                self.connections.remote_all("hit_rock")
            elif tile.type == self.game.get_terrain_type("energy") and child == "collector":
                collecting = True

            tile = self.map.get_tile((endX, endY + 1))
            if tile.type == self.game.get_terrain_type("rocks"):
                self.interrupted_tether = True                                 
                self.connections.remote_all("hit_rock")
            elif tile.type == self.game.get_terrain_type("energy") and child == "collector":
                collecting = True

            tile = self.map.get_tile((endX + 1, endY + 1))
            if tile.type == self.game.get_terrain_type("rocks"): 
                self.interrupted_tether = True                
                self.connections.remote_all("hit_rock")
            elif tile.type == self.game.get_terrain_type("energy") and child == "collector":
                collecting = True

            tile = self.map.get_tile((endX - 1, endY - 1))
            if tile.type == self.game.get_terrain_type("rocks"): 
                self.interrupted_tether = True                                 
                self.connections.remote_all("hit_rock")
            elif tile.type == self.game.get_terrain_type("energy") and child == "collector":
                collecting = True

            tile = self.map.get_tile((endX - 1, endY))
            if tile.type == self.game.get_terrain_type("rocks"): 
                self.interrupted_tether = True                 
                self.connections.remote_all("hit_rock")
            elif tile.type == self.game.get_terrain_type("energy") and child == "collector":
                collecting = True

            tile = self.map.get_tile((endX, endY - 1))
            if tile.type == self.game.get_terrain_type("rocks"): 
                self.interrupted_tether = True
                self.connections.remote_all("hit_rock")
            elif tile.type == self.game.get_terrain_type("energy") and child == "collector":
                collecting = True

            tile = self.map.get_tile((endX - 1, endY + 1))
            if tile.type == self.game.get_terrain_type("rocks"): 
                self.interrupted_tether = True
                self.connections.remote_all("hit_rock")
            elif tile.type == self.game.get_terrain_type("energy") and child == "collector":
                collecting = True

            tile = self.map.get_tile((endX + 1, endY - 1))
            if tile.type == self.game.get_terrain_type("rocks"): 
                self.interrupted_tether = True
                self.connections.remote_all("hit_rock")
            elif tile.type == self.game.get_terrain_type("energy") and child == "collector":
                collecting = True

        logging.debug("collecting = %r" % collecting)
        return (start_tile.x, start_tile.y, endX, endY, collecting)

#****************************************************************************
#Determine where a split shot lands
#****************************************************************************
    def split_trajectory(self, parentID, rotation, power, child, player, clientID):
        playerID = player.playerID[clientID]
        unit = self.map.get_unit_from_id(parentID)
        logging.info("player " + str(playerID) + " launched a " + child)
        start_tile = self.map.get_tile_from_unit(unit)
        endX = start_tile.x
        endY = start_tile.y
        self.interrupted_tether = False
        power = power + 7 #launching has minimal range, if changing don't forget to change animation distance (in networkclient.py) and find_trajectory
        a1hit = False
        a2hit = False
        a3hit = False

        for find_target in range(1, power):
            temp_rotation = self.game.deg2rad(rotation)
            midpoint = int(power - round((power / 2), 0)) #find location where shots split
            if find_target < midpoint:
                endX = find_target * math.cos(temp_rotation / 180.0 * math.pi)
                endY = find_target * math.sin(temp_rotation / 180.0 * math.pi)
                endX = round(endX, 0)
                endY = round(endY, 0)
                splitX = int(endX) + start_tile.x
                splitY = int(endY) + start_tile.y

                #code for looping the map edges
                if splitX < 0:
                    splitX = self.map.xsize + splitX
                if splitX > self.map.xsize - 1:
                    splitX = splitX - (self.map.xsize - 1)
                if splitY < 0:
                    splitY = self.map.ysize + splitY
                if splitY > self.map.ysize - 1:
                    splitY = splitY - (self.map.ysize - 1)

                #determine if shot is intercepted by either an AA or shield
                for lookD in self.map.unitstore.values():
                    if lookD.playerID != playerID and (lookD.type.id == "shield" or lookD.type.id == "antiair") and lookD.disabled == False and lookD.virused == False and lookD.reloading == False:
                        radius = self.game.get_defense_radius(lookD.type.id)
                        searchX = lookD.x
                        searchY = lookD.y
                        for find_target in range(1, radius):
                            spinner = 0
                            while spinner < 360:
                                searchX = find_target * math.cos(spinner / 180.0 * math.pi)
                                searchY = find_target * math.sin(spinner / 180.0 * math.pi)
                                searchX = round(searchX, 0)
                                searchY = round(searchY, 0)
                                searchX = int(searchX) + lookD.x
                                searchY = int(searchY) + lookD.y
                                if searchX == splitX and searchY == splitY:
                                    spinner = 360
                                    self.interrupted_tether = True
                                    self.connections.remote_all("triggered_defense", lookD.x, lookD.y, splitX, splitY, 1)
                                    if lookD.type.id == "antiair":
                                        lookD.reloading = True
                                        player.Ireloading[clientID].append(lookD.id)
                                        player.reload[clientID] = True
                                    return (start_tile.x, start_tile.y, splitX, splitY, splitX, splitY, splitX, splitY, True, True, True)
                                else:
                                    spinner = spinner + 5

            else:
                default_rotation = temp_rotation
                temp_rotation = default_rotation
                launch_step = find_target - midpoint
                if a1hit == False:
                    endX = launch_step * math.cos(temp_rotation / 180.0 * math.pi)
                    endY = launch_step * math.sin(temp_rotation / 180.0 * math.pi)
                    endX = round(endX, 0)
                    endY = round(endY, 0)
                    coordX1 = int(endX) + splitX
                    coordY1 = int(endY) + splitY

                    #code for looping the map edges
                    if coordX1 < 0:
                        coordX1 = self.map.xsize + coordX1
                    if coordX1 > self.map.xsize - 1:
                        coordX1 = coordX1 - (self.map.xsize - 1)
                    if coordY1 < 0:
                        coordY1 = self.map.ysize + coordY1
                    if coordY1 > self.map.ysize - 1:
                        coordY1 = coordY1 - (self.map.ysize - 1)

                    for lookD in self.map.unitstore.values():
                        if lookD.playerID != playerID and (lookD.type.id == "shield" or lookD.type.id == "antiair") and lookD.disabled == False and lookD.virused == False and lookD.reloading == False:
                            radius = self.game.get_defense_radius(lookD.type.id)
                            searchX = lookD.x
                            searchY = lookD.y
                            for find_intercept in range(1, radius):
                                spinner = 0
                                while spinner < 360:
                                    searchX = find_intercept * math.cos(spinner / 180.0 * math.pi)
                                    searchY = find_intercept * math.sin(spinner / 180.0 * math.pi)
                                    searchX = round(searchX, 0)
                                    searchY = round(searchY, 0)
                                    searchX = int(searchX) + lookD.x
                                    searchY = int(searchY) + lookD.y
                                    if searchX == coordX1 and searchY == coordY1:
                                        spinner = 360
                                        self.interrupted_tether = True
                                        self.connections.remote_all("triggered_defense", lookD.x, lookD.y, coordX1, coordY1, 1)
                                        a1hit = True
                                        if lookD.type.id == "antiair":
                                            lookD.reloading = True
                                            player.Ireloading[clientID].append(lookD.id)
                                            player.reload[clientID] = True
                                    else:
                                        spinner = spinner + 5

                temp_rotation = default_rotation + 45
                if temp_rotation > 360:
                    temp_rotation = default_rotation - 315

                if a2hit == False:
                    endX = launch_step * math.cos(temp_rotation / 180.0 * math.pi)
                    endY = launch_step * math.sin(temp_rotation / 180.0 * math.pi)
                    endX = round(endX, 0)
                    endY = round(endY, 0)
                    coordX2 = int(endX) + splitX
                    coordY2 = int(endY) + splitY

                    #code for looping the map edges
                    if coordX2 < 0:
                        coordX2 = self.map.xsize + coordX2
                    if coordX2 > self.map.xsize - 1:
                        coordX2 = coordX2 - (self.map.xsize - 1)
                    if coordY2 < 0:
                        coord2 = self.map.ysize + coordY2
                    if coordY2 > self.map.ysize - 1:
                        coordY2 = coordY2 - (self.map.ysize - 1)

                    for lookD in self.map.unitstore.values():
                        if lookD.playerID != playerID and (lookD.type.id == "shield" or lookD.type.id == "antiair") and lookD.disabled == False and lookD.virused == False and lookD.reloading == False:
                            radius = self.game.get_defense_radius(lookD.type.id)
                            searchX = lookD.x
                            searchY = lookD.y
                            for find_intercept in range(1, radius):
                                spinner = 0
                                while spinner < 360:
                                    searchX = find_intercept * math.cos(spinner / 180.0 * math.pi)
                                    searchY = find_intercept * math.sin(spinner / 180.0 * math.pi)
                                    searchX = round(searchX, 0)
                                    searchY = round(searchY, 0)
                                    searchX = int(searchX) + lookD.x
                                    searchY = int(searchY) + lookD.y
                                    if searchX == coordX2 and searchY == coordY2:
                                        spinner = 360
                                        self.interrupted_tether = True
                                        self.connections.remote_all("triggered_defense", lookD.x, lookD.y, coordX2, coordY2, 2)
                                        a2hit = True
                                        if lookD.type.id == "antiair":
                                            lookD.reloading = True
                                            player.Ireloading[clientID].append(lookD.id)
                                            player.reload[clientID] = True
                                    else:
                                        spinner = spinner + 5

                temp_rotation = default_rotation - 45
                if temp_rotation < 1:
                    temp_rotation = default_rotation + 315

                if a3hit == False:
                    endX = launch_step * math.cos(temp_rotation / 180.0 * math.pi)
                    endY = launch_step * math.sin(temp_rotation / 180.0 * math.pi)
                    endX = round(endX, 0)
                    endY = round(endY, 0)
                    coordX3 = int(endX) + splitX
                    coordY3 = int(endY) + splitY

                    #code for looping the map edges
                    if coordX3 < 0:
                        coordX3 = self.map.xsize + coordX3
                    if coordX3 > self.map.xsize - 1:
                        coordX3 = coordX3 - (self.map.xsize - 1)
                    if coordY3 < 0:
                        coordY3 = self.map.ysize + coordY3
                    if coordY3 > self.map.ysize - 1:
                        coordY3 = coordY3 - (self.map.ysize - 1)

                    for lookD in self.map.unitstore.values():
                        if lookD.playerID != playerID and (lookD.type.id == "shield" or lookD.type.id == "antiair") and lookD.disabled == False and lookD.virused == False and lookD.reloading == False:
                            radius = self.game.get_defense_radius(lookD.type.id)
                            searchX = lookD.x
                            searchY = lookD.y
                            for find_intercept in range(1, radius):
                                spinner = 0
                                while spinner < 360:
                                    searchX = find_intercept * math.cos(spinner / 180.0 * math.pi)
                                    searchY = find_intercept * math.sin(spinner / 180.0 * math.pi)
                                    searchX = round(searchX, 0)
                                    searchY = round(searchY, 0)
                                    searchX = int(searchX) + lookD.x
                                    searchY = int(searchY) + lookD.y
                                    if searchX == coordX3 and searchY == coordY3:
                                        spinner = 360
                                        self.interrupted_tether = True
                                        self.connections.remote_all("triggered_defense", lookD.x, lookD.y, coordX3, coordY3, 3)
                                        a3hit = True
                                        if lookD.type.id == "antiair":
                                            lookD.reloading = True
                                            player.Ireloading[clientID].append(lookD.id)
                                            player.reload[clientID] = True
                                    else:
                                        spinner = spinner + 5

        return (start_tile.x, start_tile.y, coordX1, coordY1, coordX2, coordY2, coordX3, coordY3, a1hit, a2hit, a3hit)



#****************************************************************************
#Find out if a unit is hit or not
#****************************************************************************
    def determine_hit(self, unit, pos, player, clientID):
        x, y = pos
        power = self.game.get_unit_power(unit)
        radius = self.game.get_unit_radius(unit) + 1
        nohit = False
        didhit = False

        for target in self.map.unitstore.values():
            target.blasted = False #clearing all targets
            if target.id == self.game.unit_counter:
                unit_class = target
                if target.disabled == True:
                    nohit = True

        if unit == "emp" and nohit == False: #processes damage of direct hit EMP's
            d_radius = self.game.get_unit_radius("bomb") + 1
            endX = x
            endY = y
            for find_target in range(0, d_radius):
                spinner = 0
                while spinner < 360:
                    if find_target == 0:
                        endX = x
                        endY = y
                        spinner = 355
                    else:
                        endX = find_target * math.cos(spinner / 180.0 * math.pi)
                        endY = find_target * math.sin(spinner / 180.0 * math.pi)
                        endX = round(endX, 0)
                        endY = round(endY, 0)
                        endX = int(endX) + x
                        endY = int(endY) + y
                    logging.debug("Radius, Spinner = %s, %s" % (find_target, spinner))
                    for target in self.map.unitstore.values():
                        logging.debug("comparing possible targets: %s, %s - %s, %s" % (endX, endY, target.x, target.y))
                        if target.x == endX and target.y == endY and (target.typeset == "build" or target.type.id == "crawler") and target.blasted == False:
                            logging.info("hit target for %s" % power)
                            target.hp = target.hp - power
                            target.blasted = True
                    spinner = spinner + 5

        for target in self.map.unitstore.values():
            target.blasted = False #clearing all targets

        if unit == "crawler" or unit == "mines":
            endX = x
            endY = y
            for target in self.map.unitstore.values():
                if target.x == endX and target.y == endY and (target.typeset == "build" or target.typeset == "tether" or target.typeset == "weap"):
                    unit_class.hp = 0 #if crawler or mine lands on something it auto detonates to avoid glitch

        if unit != "crawler" and unit != "mines" and nohit == False:
            endX = x
            endY = y
            for find_target in range(0, radius):
                spinner = 0
                while spinner < 360:
                    if find_target == 0:
                        endX = x
                        endY = y
                        spinner = 355
                    else:
                        endX = find_target * math.cos(spinner / 180.0 * math.pi)
                        endY = find_target * math.sin(spinner / 180.0 * math.pi)
                        endX = round(endX, 0)
                        endY = round(endY, 0)
                        endX = int(endX) + x
                        endY = int(endY) + y
                    logging.debug("Radius, Spinner = %s, %s" % (find_target, spinner))
                    for target in self.map.unitstore.values():
                        logging.debug("comparing possible targets: %s, %s - %s, %s" % (endX, endY, target.x, target.y))
                        if target.x == endX and target.y == endY and (target.typeset == "build" or target.type.id == "crawler") and target.blasted == False:
                            logging.info("detected hit")
                            didhit = True
                            if unit == "emp":
                                target.disabled = True
                                target.blasted = True
                                player.Idisabled[clientID].append(target.id)
                                player.undisable[clientID] = True
                                logging.info("you disabled a %r" % target.type.id)
                            elif unit == "repair":
                                logging.info("repaired target for 1")
                                target.hp = target.hp + 1
                                target.blasted = True
                                logging.info("it's current HP = %s" % target.hp)
                                if target.hp > self.game.get_unit_hp(target.type.id):
                                    target.hp = self.game.get_unit_hp(target.type.id) #prevent units from going over max HP
                            elif unit == "spike": #spike on a building
                                target.hp = target.hp - power
                                for target2 in self.map.unitstore.values(): #if direct hit on building, parent unit gets zapped
                                    if target2.id == target.parentID:
                                        target2.hp = target2.hp - 1
                                target.blasted = True
                            elif unit == "virus":
                                target.virused = True
                                target.just_virused = True
                                target.was_virused = False
                                target.was_virused2 = False
                                target.blasted = True
                            elif unit == "recall":
                                if target.playerID == player.playerID: #if own target, insta-death
                                    player.energy[clientID] = player.energy[clientID] + target.hp
                                    target.hp = 0
                                    target.blasted = True
                                    target.disabled = True
                                else:
                                    if target.hp < 3: #if not own target
                                        player.energy[clientID] = player.energy[clientID] + target.hp
                                        target.hp = 0
                                        target.blasted = True
                                        target.disabled = True
                                    else:
                                        player.energy[clientID] = player.energy[clientID] + power
                                        target.hp = target.hp - power
                                        target.blasted = True
                                        target.disabled = True
                            else:
                                logging.info("hit target for %s" % power)
                                target.hp = target.hp - power
                                target.blasted = True
                        elif target.x == endX and target.y == endY and target.typeset == "tether" and unit == "spike": #spikes landing on tethers zaps buildings on both ends
                            didhit = True
                            (target1, target2) = self.game.find_tether_ends(target)
                            for tetherend in self.map.unitstore.values():
                                if tetherend.id == target1 or tetherend.id == target2:
                                    tetherend.hp = tetherend.hp - 1
                                    logging.info("spike damaged unit %s" % tetherend.id)
                            return #spikes only affect one tether, so when one tether is hit, no further damage is calculated
                    if didhit == False and unit != "emp":
                        unit_class.disabled = True #weapon missed and so is disabled

                    spinner = spinner + 5

#****************************************************************************
#calculate the number of players currently connected to the game
#****************************************************************************
    def max_players(self):
        totalplayers = len(self.playerIDs)
        return totalplayers

#****************************************************************************
#calculate the number of clients currently connected to the game
#****************************************************************************
    def max_clients(self, clients):
        q = 0
        placeholder = 0
        for q in clients:
            placeholder = placeholder + 1
        return placeholder

#****************************************************************************
#Calculate the amount of energy per player
#****************************************************************************
    def calculate_energy(self, playerID, energy):
        energy = energy + 7
        for unit in self.map.unitstore.values():
            if unit.playerID == playerID and unit.type.id == "collector" and unit.disabled == False:
                energy = energy + 1
                if unit.collecting == True:
                    energy = energy + 2
        if energy > 35:
            energy = 35
        return energy


#****************************************************************************
#
#****************************************************************************
    def setup_network(self):
        self.connections = ConnectionHandler(self)
        portal = Portal(self.connections)
        checker = InMemoryUsernamePasswordDatabaseDontUse()
        checker.addUser("guest", "guest")
        portal.registerChecker(checker)
        reactor.listenTCP(6112, pb.PBServerFactory(portal))


#****************************************************************************
#
#****************************************************************************
    def run_network(self):

        reactor.run()

