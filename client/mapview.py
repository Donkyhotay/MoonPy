"""Copyright 2009:
    Isaac Carroll, Kevin Clement, Jon Handy, David Carroll, Daniel Carroll

This program is free software you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
"""

import os, sys
import pygame
import time
import logging
import math
import random
from pygame.locals import *
from cursors import *
from common.map import *


#****************************************************************************
# The Mapview class contains all logic for rendering maps.
#****************************************************************************
class Mapview:

    def __init__(self, clientstate):
        self.client = clientstate
        self.map = clientstate.map
        for unit in self.map.unitstore.values(): #finds starting position and places it over starting hub
            if unit.playerID == self.client.playerID[self.client.clientID]:
                self.view_x = unit.x - 14
                self.view_y = unit.y - 14

        self.tileset = self.client.tileset
        self.rect = pygame.Rect(0,0,self.client.screen_width - self.tileset.panel_width, self.client.screen_height - self.tileset.panel_height)
 

#****************************************************************************
# Draws the entire map to the screen.
#****************************************************************************
    def drawmap(self):
        self.delta_scroll()
        mapcoord_list = self.gui_rect_iterate(self.view_x, self.view_y)


        if self.client.heldbutton == "right":
            self.client.holdbutton.rotateright()
        if self.client.heldbutton == "left":
            self.client.holdbutton.rotateleft()
        if self.client.heldbutton == "increase":
            self.client.holdbutton.increasepower()
        if self.client.heldbutton == "decrease":
            self.client.holdbutton.decreasepower()


        #this order determines layering of the map, terrain is on the bottom, then doodads, then tethers, then units, last are the indicators which are above everything except for the selected unit
        for pos in mapcoord_list:
            self.draw_tile_terrain(pos)
        for pos in mapcoord_list:
            self.draw_doodad(pos)
        for pos in mapcoord_list:
            self.draw_tether(pos)
        for pos in mapcoord_list:
            self.draw_unit(pos)
        for pos in mapcoord_list:
            self.draw_indicators(pos)
    
        if self.client.launched == True:
            self.show_launch()

        if self.client.dying_unit == True:
            self.show_explosion()

        self.draw_mapview_selection()
        self.tileset.animation_next()

#****************************************************************************
# Draws a single map tile with terrain to the mapview canvas.
#****************************************************************************
    def draw_tile_terrain(self, pos):
        map_x, map_y = pos
        real_map_x = map_x % self.map.xsize
        real_map_y = map_y % self.map.ysize

        tile = self.map.get_tile((real_map_x, real_map_y))
        gui_x, gui_y = self.map_to_gui(pos)
        if not self.tileset.is_edge_tile(tile):
            surface = self.tileset.get_terrain_surf_from_tile(tile)
            if not surface: return
            blit_x = gui_x
            blit_y = gui_y
            blit_width = surface.get_width() 

            blit_height = surface.get_height()

            self.client.screen.blit(surface, (blit_x, blit_y), [0,0, blit_width, blit_height])
            return 
        else:
            (surface1, surface2, surface3, surface4) = self.tileset.get_edge_surf_from_tile(tile)
            blit_width = surface1.get_width() 
            blit_height = surface1.get_height()
            blit_x = gui_x - self.view_x 
            blit_y = gui_y - self.view_y


            self.client.screen.blit(surface1, (blit_x + self.tileset.tile_width / 4, blit_y - self.tileset.tile_height / 3), [0,0, blit_width, blit_height])
            self.client.screen.blit(surface2, (blit_x + self.tileset.tile_width / 2, blit_y - self.tileset.tile_height / 10), [0,0, blit_width, blit_height])
            self.client.screen.blit(surface3, (blit_x + self.tileset.tile_width / 4, blit_y + self.tileset.tile_height / 6), [0,0, blit_width, blit_height])
            self.client.screen.blit(surface4, (blit_x, blit_y - self.tileset.tile_height / 10), [0,0, blit_width, blit_height])

#****************************************************************************
# Draws doodads to canvas view
#****************************************************************************
    def draw_doodad(self, map_pos):
        real_map_pos = self.map.wrap_map_pos(map_pos)
        unit = self.map.get_doodad(real_map_pos) 
        if not unit:
            return 
        if unit.typeset != "doodad":
            return

        #draw units themselves
        gui_x, gui_y = self.map_to_gui(map_pos)

        #unit_surface = self.tileset.get_unit_surf_from_tile(unit.type.id, 0, unit.playerID)
        unit_surface = self.tileset.get_unit_surf_from_tile(unit.type.id, 0, self.client.game.get_unit_team(self.client.playerID[self.client.clientID], unit.playerID, self.client.teamID[self.client.clientID]))

        blit_x = gui_x
        blit_y = gui_y
        self.client.screen.blit(unit_surface, (blit_x, blit_y))

#****************************************************************************
# Draws tethers to canvas view
#****************************************************************************
    def draw_tether(self, map_pos):
        real_map_pos = self.map.wrap_map_pos(map_pos)
        unit = self.map.get_unit(real_map_pos) 
        if not unit:
            return
        if unit.typeset != "tether": 
            return

        #draw units themselves
        gui_x, gui_y = self.map_to_gui(map_pos)

        if self.client.tetherplace == unit.glow_tether:
            tetherglow = "t1"
        else:
            tetherglow = "t2"

        unit_surface = self.tileset.get_unit_surf_from_tile(tetherglow, 0, self.client.game.get_unit_team(self.client.playerID[self.client.clientID], unit.playerID, self.client.teamID[self.client.clientID]))

        blit_x = gui_x
        blit_y = gui_y
        self.client.screen.blit(unit_surface, (blit_x, blit_y))

#****************************************************************************
# Draws a single map tile with a unit to the mapview canvas.
#****************************************************************************
    def draw_unit(self, map_pos):
        real_map_pos = self.map.wrap_map_pos(map_pos)
        unit = self.map.get_unit(real_map_pos) 

        if not unit:
            return 
        if unit.typeset == "tether":
            return

        #draw units themselves
        gui_x, gui_y = self.map_to_gui(map_pos)

        #unit_surface = self.tileset.get_unit_surf_from_tile(unit.type.id, 0, unit.playerID)
        unit_surface = self.tileset.get_unit_surf_from_tile(unit.type.id, 0, self.client.game.get_unit_team(self.client.playerID[self.client.clientID], unit.playerID, self.client.teamID[self.client.clientID]))

        blit_x = gui_x
        blit_y = gui_y
        if unit.typeset == "build": #centering 3x3 graphics
            blit_x = gui_x - 24 
            blit_y = gui_y - 24

        self.client.screen.blit(unit_surface, (blit_x, blit_y))
        if unit.virused == True:
            status_surface = self.tileset.get_unit_surf_from_tile("virus_status", 0, 3)
            self.client.screen.blit(status_surface, (blit_x, blit_y))
        if unit.disabled == True or unit.reloading == True:
            status_surface = self.tileset.get_unit_surf_from_tile("disable_status", 0, 3)
            self.client.screen.blit(status_surface, ((blit_x + 48), blit_y))
            

#****************************************************************************
# Draws the rotator
#****************************************************************************
    def draw_indicators(self, map_pos):
        real_map_pos = self.map.wrap_map_pos(map_pos)
        unit = self.map.get_unit(real_map_pos) 

        if not unit:
            return 

        #draw units themselves
        gui_x, gui_y = self.map_to_gui(map_pos)

        blit_x = gui_x
        blit_y = gui_y

        if unit.type.id == "mines":
            tempX = blit_x + 12
            tempY = blit_y + 12
            scale = self.client.game.get_defense_radius("mines") * 24
            colorID = self.client.game.get_unit_team(self.client.playerID[self.client.clientID], unit.playerID, self.client.teamID[self.client.clientID])
            teamcolor = self.client.game.get_unit_color(colorID)
            pygame.draw.circle(self.client.screen, teamcolor , (tempX, tempY), scale, 1)

        if unit.type.id == "shield":
            tempX = blit_x + 12
            tempY = blit_y + 12
            scale = self.client.game.get_defense_radius("shield") * 24
            colorID = self.client.game.get_unit_team(self.client.playerID[self.client.clientID], unit.playerID, self.client.teamID[self.client.clientID])
            teamcolor = self.client.game.get_unit_color(colorID)
            pygame.draw.circle(self.client.screen, teamcolor, (tempX, tempY), scale, 1)

        if unit.type.id == "antiair":
            tempX = blit_x + 12
            tempY = blit_y + 12
            scale = self.client.game.get_defense_radius("antiair") * 24
            colorID = self.client.game.get_unit_team(self.client.playerID[self.client.clientID], unit.playerID, self.client.teamID[self.client.clientID])
            teamcolor = self.client.game.get_unit_color(colorID)
            pygame.draw.circle(self.client.screen, teamcolor, (tempX, tempY), scale, 1)

        if unit.type.id == "crawler":
            for show_health in range(1, unit.hp + 1):
                blit_x = gui_x 
                blit_y = gui_y
                colorID = self.client.game.get_unit_team(self.client.playerID[self.client.clientID], unit.playerID, self.client.teamID[self.client.clientID])
                teamcolor = self.client.game.get_unit_color(colorID)
                pygame.draw.line(self.client.screen, teamcolor, (blit_x + (show_health * 10), blit_y + 72), (blit_x + (show_health * 10), blit_y + 62), 5)

        if unit.typeset == "build":
            for show_health in range(1, unit.hp + 1):
                blit_x = gui_x - 24 
                blit_y = gui_y - 24
                colorID = self.client.game.get_unit_team(self.client.playerID[self.client.clientID], unit.playerID, self.client.teamID[self.client.clientID])
                teamcolor = self.client.game.get_unit_color(colorID)
                pygame.draw.line(self.client.screen, teamcolor, (blit_x + (show_health * 10), blit_y + 72), (blit_x + (show_health * 10), blit_y + 62), 5)
            

        #find and show rotation indicator on selected unit
        for selected in self.client.selected_unit.values():
            if unit.id == selected.id:
                unit_surface = self.tileset.get_unit_surf_from_tile(unit.type.id, 0, self.client.game.get_unit_team(self.client.playerID[self.client.clientID], unit.playerID, self.client.teamID[self.client.clientID]))
                blit_x = gui_x - 24 
                blit_y = gui_y - 24
                rotation = self.client.rotate_position[self.client.clientID]
                endX = unit.x
                endY = unit.y
                startX = blit_x + 36
                startY = blit_y + 36
                temp_rotation = self.client.game.deg2rad(rotation)
                endX = 175 * math.cos(temp_rotation / 180.0 * math.pi)
                endY = 175 * math.sin(temp_rotation / 180.0 * math.pi)
                finalX = endX + startX + 1
                finalY = endY + startY + 1
                pygame.draw.line(self.client.screen, (255, 10, 10), (startX, startY), (finalX, finalY), 1)
                self.client.screen.blit(unit_surface, (blit_x, blit_y))
                if unit.typeset == "build":
                    for show_health in range(1, unit.hp + 1):
                        colorID = self.client.game.get_unit_team(self.client.playerID[self.client.clientID], unit.playerID, self.client.teamID[self.client.clientID])
                        teamcolor = self.client.game.get_unit_color(colorID)
                        pygame.draw.line(self.client.screen, teamcolor, (blit_x + (show_health * 10), blit_y + 72), (blit_x + (show_health * 10), blit_y + 62), 5)
                if unit.virused == True:
                    status_surface = self.tileset.get_unit_surf_from_tile("virus_status", 0, 3)
                    self.client.screen.blit(status_surface, (blit_x, blit_y))
                if unit.disabled == True:
                    status_surface = self.tileset.get_unit_surf_from_tile("disable_status", 0, 3)
                    self.client.screen.blit(status_surface, ((blit_x + 48), blit_y))


#****************************************************************************
# Divides n by d
#****************************************************************************
    def divide(self, n, d):
        res = 0
        if ( (n) < 0 and (n) % (d) < 0 ):
            res = 1
        return ((n / d ) - res)

#****************************************************************************
# Increments the mapview scrolling (moves one step).
#****************************************************************************
    def delta_scroll(self):
        self.view_x += (self.client.view_delta_x / 10)
        self.view_y += (self.client.view_delta_y / 10)

#****************************************************************************
# Centers the view on a specified tile.
#****************************************************************************
    def center_view_on_tile(self, map_pos):
        x, y = map_pos
        self.view_x = x - 16
        self.view_y = y - 16


#****************************************************************************
#
#****************************************************************************
    def draw_mapview_selection(self):

        if self.client.mapctrl.mouse_state == 'select':
            (left, top) = self.client.mapctrl.select_pos_start
            (right, bottom) = self.client.mapctrl.select_pos_end
            height = bottom - top
            width = right - left
            sel_rect = pygame.Rect(left, top, width, height)
            pygame.draw.rect(self.client.screen, (255,0,0), sel_rect, 1)

#****************************************************************************
# Returns gui-coordinates (eg. screen) from map-coordinates (a map tile).
#****************************************************************************
    def map_to_gui(self, map_pos):
        map_dx, map_dy = map_pos
        map_dx = map_dx - (self.view_x)
        map_dy = map_dy - (self.view_y)
        return (map_dx * self.tileset.tile_width, map_dy * self.tileset.tile_height)


#****************************************************************************
# Returns map-coordinates from gui-coordinates.
#****************************************************************************
    def gui_to_map(self, gui_pos):
        gui_x, gui_y = gui_pos
        map_x = self.divide(gui_x, self.tileset.tile_width)
        map_y = self.divide(gui_y, self.tileset.tile_height)
        endX = map_x + self.view_x
        endY = map_y + self.view_y
        if endX < 0:
            endX = self.map.xsize + endX
        if endX > self.map.xsize - 1:
            endX = endX - (self.map.xsize - 1)
        if endY < 0:
            endY = self.map.ysize + endY
        if endY > self.map.ysize - 1:
            endY = endY - (self.map.ysize - 1)
        return (endX, endY)

#****************************************************************************
# Returns a list of map coordinates to be shows on the map canvas view.
#****************************************************************************
    def gui_rect_iterate(self, gui_x0, gui_y0):
        mapcoord_list = []
        for map_x in range(gui_x0, (gui_x0 + 29)):
            for map_y in range(gui_y0, (gui_y0 + 29)):
                mapcoord_list.insert(0, (map_x, map_y))
            
        return mapcoord_list

#****************************************************************************
# Displays launched unit
#****************************************************************************
    def show_launch(self):
        if self.client.launch_type == "cluster" or self.client.launch_type == "mines":
            if self.client.launch_step < self.client.launch_distance - 1:
                self.client.launch_step = self.client.launch_step + .5
                temp_rotation = self.client.game.deg2rad(self.client.launch_direction)
                midpoint = int(self.client.launch_distance - round((self.client.launch_distance / 2), 0))
                if self.client.launch_step < midpoint:
                    endX = self.client.launch_step * math.cos(temp_rotation / 180.0 * math.pi)
                    endY = self.client.launch_step * math.sin(temp_rotation / 180.0 * math.pi)
                    endX = endX + self.client.launch_startx
                    endY = endY + self.client.launch_starty
                    self.client.launch_splitx = endX
                    self.client.launch_splity = endY
                    map_pos = endX, endY
                    unit_surface = self.tileset.get_unit_surf_from_tile(self.client.launch_type, 0, self.client.game.get_unit_team(self.client.playerID[self.client.clientID], self.client.playerlaunched, self.client.teamID[self.client.clientID]))
                    blit_x, blit_y = self.map_to_gui(map_pos)
                    self.client.screen.blit(unit_surface, (blit_x, blit_y))
                    blit_x = blit_x + 24
                    self.client.screen.blit(unit_surface, (blit_x, blit_y))
                    blit_y = blit_y + 24
                    blit_x = blit_x - 12
                    self.client.screen.blit(unit_surface, (blit_x, blit_y))
                    #code for looping the map edges
                    if endX < 0:
                        endX = self.map.xsize + endX
                    if endX > self.map.xsize - 1:
                        endX = endX - (self.map.xsize - 1)
                    if endY < 0:
                        endY = self.map.ysize + endY
                    if endY > self.map.ysize - 1:
                        endY = endY - (self.map.ysize - 1)
                    if self.client.intercepted == True and round(endX) == self.client.tarX and round(endY) == self.client.tarY:
                        self.client.intercepted = False
                        self.client.moonaudio.sound("laser.ogg")
                        self.client.launched = False
                        self.client.landed = True
                        self.client.launch_step = 1
                        self.client.hit1 = True
                        self.client.hit2 = True
                        self.client.hit3 = True
                        defX, defY = self.map_to_gui((self.client.defX, self.client.defY))
                        tarX, tarY = self.map_to_gui((self.client.tarX, self.client.tarY))
                        defX = defX + 12
                        defY = defY + 12
                        pygame.draw.line(self.client.screen, (255, 255, 255), (defX, defY), (tarX, tarY), 4)
                else:
                    #splitting the cluster
                    launch_step = self.client.launch_step - midpoint
                    if self.client.hit1 == False:
                        endX = launch_step * math.cos(temp_rotation / 180.0 * math.pi)
                        endY = launch_step * math.sin(temp_rotation / 180.0 * math.pi)
                        endX = endX + self.client.launch_splitx
                        endY = endY + self.client.launch_splity
                        map_pos = endX, endY
                        blit_x, blit_y = self.map_to_gui(map_pos)
                        unit_surface = self.tileset.get_unit_surf_from_tile(self.client.launch_type, 0, self.client.game.get_unit_team(self.client.playerID[self.client.clientID], self.client.playerlaunched, self.client.teamID[self.client.clientID]))
                        self.client.screen.blit(unit_surface, (blit_x, blit_y))
                        #code for looping the map edges
                        if endX < 0:
                            endX = self.map.xsize + endX
                        if endX > self.map.xsize - 1:
                            endX = endX - (self.map.xsize - 1)
                        if endY < 0:
                            endY = self.map.ysize + endY
                        if endY > self.map.ysize - 1:
                            endY = endY - (self.map.ysize - 1)
                        if self.client.intercepted == True and round(endX) == self.client.tarX and round(endY) == self.client.tarY:
                            self.client.intercepted = False
                            self.client.hit1 = True
                            self.client.moonaudio.sound("laser.ogg")
                            defX, defY = self.map_to_gui((self.client.defX, self.client.defY))
                            tarX, tarY = self.map_to_gui((self.client.tarX, self.client.tarY))
                            defX = defX + 12
                            defY = defY + 12
                            pygame.draw.line(self.client.screen, (255, 255, 255), (defX, defY), (tarX, tarY), 4)

                    default_rotation = temp_rotation

                    temp_rotation = default_rotation + 45
                    if temp_rotation > 360:
                        temp_rotation = default_rotation - 315

                    launch_step = self.client.launch_step - midpoint
                    if self.client.hit2 == False:
                        endX = launch_step * math.cos(temp_rotation / 180.0 * math.pi)
                        endY = launch_step * math.sin(temp_rotation / 180.0 * math.pi)
                        endX = endX + self.client.launch_splitx
                        endY = endY + self.client.launch_splity
                        map_pos = endX, endY
                        blit_x, blit_y = self.map_to_gui(map_pos)
                        unit_surface = self.tileset.get_unit_surf_from_tile(self.client.launch_type, 0, self.client.game.get_unit_team(self.client.playerID[self.client.clientID], self.client.playerlaunched, self.client.teamID[self.client.clientID]))
                        self.client.screen.blit(unit_surface, (blit_x, blit_y))
                        #code for looping the map edges
                        if endX < 0:
                            endX = self.map.xsize + endX
                        if endX > self.map.xsize - 1:
                            endX = endX - (self.map.xsize - 1)
                        if endY < 0:
                            endY = self.map.ysize + endY
                        if endY > self.map.ysize - 1:
                            endY = endY - (self.map.ysize - 1)
                        if self.client.intercepted2 == True and round(endX) == self.client.tarX2 and round(endY) == self.client.tarY2:
                            self.client.intercepted2 = False
                            self.client.hit2 = True
                            self.client.moonaudio.sound("laser.ogg")
                            defX, defY = self.map_to_gui((self.client.defX2, self.client.defY2))
                            tarX, tarY = self.map_to_gui((self.client.tarX2, self.client.tarY2))
                            defX = defX + 12
                            defY = defY + 12
                            pygame.draw.line(self.client.screen, (255, 255, 255), (defX, defY), (tarX, tarY), 4)

                    temp_rotation = default_rotation - 45
                    if temp_rotation < 1:
                        temp_rotation = default_rotation + 315

                    launch_step = self.client.launch_step - midpoint
                    if self.client.hit3 == False:
                        endX = launch_step * math.cos(temp_rotation / 180.0 * math.pi)
                        endY = launch_step * math.sin(temp_rotation / 180.0 * math.pi)
                        endX = endX + self.client.launch_splitx
                        endY = endY + self.client.launch_splity
                        map_pos = endX, endY
                        blit_x, blit_y = self.map_to_gui(map_pos)
                        unit_surface = self.tileset.get_unit_surf_from_tile(self.client.launch_type, 0, self.client.game.get_unit_team(self.client.playerID[self.client.clientID], self.client.playerlaunched, self.client.teamID[self.client.clientID]))
                        self.client.screen.blit(unit_surface, (blit_x, blit_y))
                        #code for looping the map edges
                        if endX < 0:
                            endX = self.map.xsize + endX
                        if endX > self.map.xsize - 1:
                            endX = endX - (self.map.xsize - 1)
                        if endY < 0:
                            endY = self.map.ysize + endY
                        if endY > self.map.ysize - 1:
                            endY = endY - (self.map.ysize - 1)
                        if self.client.intercepted3 == True and round(endX) == self.client.tarX3 and round(endY) == self.client.tarY3:
                            self.client.intercepted3 = False
                            self.client.hit3 = True
                            self.client.moonaudio.sound("laser.ogg")
                            defX, defY = self.map_to_gui((self.client.defX3, self.client.defY3))
                            tarX, tarY = self.map_to_gui((self.client.tarX3, self.client.tarY3))
                            defX = defX + 12
                            defY = defY + 12
                            pygame.draw.line(self.client.screen, (255, 255, 255), (defX, defY), (tarX, tarY), 4)

            else: 
                if self.client.launch_type == "mines":
                    self.client.moonaudio.sound("landing.ogg")
                self.client.launched = False
                self.client.landed = True
                self.client.launch_step = 1
            return

        if self.client.launch_type == "missile":
            if self.client.launch_step < self.client.launch_distance - 1:
                self.client.launch_step = self.client.launch_step + .5
                temp_rotation = self.client.game.deg2rad(self.client.launch_direction)
                endX = self.client.launch_step * math.cos(temp_rotation / 180.0 * math.pi)
                endY = self.client.launch_step * math.sin(temp_rotation / 180.0 * math.pi)
                endX = endX + self.client.launch_startx
                endY = endY + self.client.launch_starty
                map_pos = endX, endY

                #find possible trajectory change in midflight
                radius = 6
                searchX = endX
                searchY = endY
                if self.client.missilelock == False:
                    for find_target in range(1, radius):
                        spinner = 0
                        while spinner < 360:
                            searchX = find_target * math.cos(spinner / 180.0 * math.pi)
                            searchY = find_target * math.sin(spinner / 180.0 * math.pi)
                            searchX = round(searchX, 0)
                            searchY = round(searchY, 0)
                            searchX = int(searchX) + int(endX)
                            searchY = int(searchY) + int(endY)
                            for target in self.map.unitstore.values():
                                if target.playerID != self.client.playerID and searchX == target.x and searchY == target.y and target.typeset == "build":
                                    #found a target and changing trajectory to hit it
                                    self.client.moonaudio.sound("lockon.ogg")
                                    self.client.missilelock = True
                                    self.client.launch_startx = endX
                                    self.client.launch_starty = endY
                                    self.client.launch_distance = find_target - 5
                                    self.client.launch_step = 1
                                    self.client.launch_direction = self.client.game.rad2deg(spinner)
                                    self.client.launch_direction = spinner + 90
                                    if self.client.launch_direction > 359:
                                        self.client.launch_direction = self.client.launch_direction - 270
                                    spinner = 360
                                    
                            else:
                                spinner = spinner + 5

                blit_x, blit_y = self.map_to_gui(map_pos)
                unit_surface = self.tileset.get_unit_surf_from_tile(self.client.launch_type, 0, self.client.game.get_unit_team(self.client.playerID[self.client.clientID], self.client.playerlaunched, self.client.teamID[self.client.clientID]))
                self.client.screen.blit(unit_surface, (blit_x, blit_y))
                #code for looping the map edges
                if endX < 0:
                    endX = self.map.xsize + endX
                if endX > self.map.xsize - 1:
                    endX = endX - (self.map.xsize - 1)
                if endY < 0:
                    endY = self.map.ysize + endY
                if endY > self.map.ysize - 1:
                    endY = endY - (self.map.ysize - 1)
                if self.client.intercepted == True and round(endX) == self.client.tarX and round(endY) == self.client.tarY:
                    self.client.intercepted = False
                    self.client.moonaudio.sound("laser.ogg")
                    self.client.launched = False
                    self.client.landed = True
                    self.client.launch_step = 1
                    defX, defY = self.map_to_gui((self.client.defX, self.client.defY))
                    tarX, tarY = self.map_to_gui((self.client.tarX, self.client.tarY))
                    defX = defX + 12
                    defY = defY + 12
                    pygame.draw.line(self.client.screen, (255, 255, 255), (defX, defY), (tarX, tarY), 4)
                return
            else: 
                if self.client.splashed == True:
                    self.client.moonaudio.sound("watersplash.ogg")
                    self.client.splashed = False
                self.client.launched = False
                self.client.landed = True
                self.client.launch_step = 1
            return

        else:
            if self.client.launch_step < self.client.launch_distance - 1:
                self.client.launch_step = self.client.launch_step + .5
                temp_rotation = self.client.game.deg2rad(self.client.launch_direction)
                endX = self.client.launch_step * math.cos(temp_rotation / 180.0 * math.pi)
                endY = self.client.launch_step * math.sin(temp_rotation / 180.0 * math.pi)
                endX = endX + self.client.launch_startx
                endY = endY + self.client.launch_starty
                map_pos = endX, endY
                blit_x, blit_y = self.map_to_gui(map_pos)
                if self.client.game.get_unit_typeset(self.client.launch_type) == "build":
                    blit_x = blit_x - 24
                    blit_y = blit_y - 24
                unit_surface = self.tileset.get_unit_surf_from_tile(self.client.launch_type, 0, self.client.game.get_unit_team(self.client.playerID[self.client.clientID], self.client.playerlaunched, self.client.teamID[self.client.clientID]))
                self.client.screen.blit(unit_surface, (blit_x, blit_y))
                #code for looping the map edges
                if endX < 0:
                    endX = self.map.xsize + endX
                if endX > self.map.xsize - 1:
                    endX = endX - (self.map.xsize - 1)
                if endY < 0:
                    endY = self.map.ysize + endY
                if endY > self.map.ysize - 1:
                    endY = endY - (self.map.ysize - 1)
                if self.client.intercepted == True and round(endX) == self.client.tarX and round(endY) == self.client.tarY:
                    self.client.intercepted = False
                    self.client.moonaudio.sound("laser.ogg")
                    self.client.launched = False
                    self.client.landed = True
                    self.client.launch_step = 1
                    defX, defY = self.map_to_gui((self.client.defX, self.client.defY))
                    tarX, tarY = self.map_to_gui((self.client.tarX, self.client.tarY))
                    defX = defX + 12
                    defY = defY + 12
                    pygame.draw.line(self.client.screen, (255, 255, 255), (defX, defY), (tarX, tarY), 4)
                return
            else: 
                if self.client.splashed == True:
                    self.client.moonaudio.sound("watersplash.ogg")
                    self.client.splashed = False
                elif self.client.hit_rock == True:
                    self.client.moonaudio.sound("mediumboom.ogg")
                    self.client.hit_rock = False
                elif self.client.game.get_unit_typeset(self.client.launch_type) == "build":
                    self.client.moonaudio.sound("landing.ogg")
                if self.client.collecting_energy == True:
                    self.client.moonaudio.sound("recall.ogg")
                    self.client.moonaudio.narrate("capture.ogg")
                    self.client.collecting_energy = False
                self.client.launched = False
                self.client.landed = True
                self.client.launch_step = 1
            return

#****************************************************************************
# Displays explosions
#****************************************************************************
    def show_explosion(self):

        place = 0
        for deathname in self.client.deathname:
            map_pos = self.client.deathX[place], self.client.deathY[place]
            blitX, blitY = self.map_to_gui(map_pos)
            blitX2 = blitX + (self.map.xsize * self.tileset.tile_width)
            blitX3 = blitX - (self.map.xsize * self.tileset.tile_width)
            blitY2 = blitY + (self.map.ysize * self.tileset.tile_height)
            blitY3 = blitY - (self.map.ysize * self.tileset.tile_height)
            unit_surface = self.tileset.get_unit_surf_from_tile(deathname, 0, self.client.game.get_unit_team(self.client.playerID[self.client.clientID], self.client.deathplayerID[place], self.client.teamID[self.client.clientID]))
            if self.client.deathtypes[place] != "weap" or deathname != "recall":
                if self.client.deathtypes[place] == "build":
                    blitX = blitX - 24
                    blitY = blitY - 24
                self.client.screen.blit(unit_surface, (blitX, blitY))
                self.client.screen.blit(unit_surface, (blitX2, blitY))
                self.client.screen.blit(unit_surface, (blitX3, blitY))
                self.client.screen.blit(unit_surface, (blitX, blitY2))
                self.client.screen.blit(unit_surface, (blitX, blitY3))
            place = place + 1
        unittype = self.client.deathtypes.pop(0)
        deathX = self.client.deathX.pop(0)
        deathY = self.client.deathY.pop(0)
        deathplayerid = self.client.deathplayerID.pop(0)
        deathname = self.client.deathname.pop(0)
        deathdisabled = self.client.deathdisabled.pop(0)
        radius = self.client.game.get_unit_radius(deathname)
        #there are 5 explosions displayed, 1 in the center and 4 exactly one map apart in case the explosion loops the map
        if unittype == "build":
            self.client.moonaudio.sound("biggestboom.ogg")
            map_pos = deathX, deathY
            blitX, blitY = self.map_to_gui(map_pos)
            blitX = blitX + 12
            blitY = blitY + 12
            blitX2 = blitX + (self.map.xsize * self.tileset.tile_width)
            blitX3 = blitX - (self.map.xsize * self.tileset.tile_width)
            blitY2 = blitY + (self.map.ysize * self.tileset.tile_height)
            blitY3 = blitY - (self.map.ysize * self.tileset.tile_height)
            scale = 0
            while scale < (radius * 24):
                scale = scale + 1
                pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY), scale, 0)
                pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX2, blitY), scale, 0)
                pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX3, blitY), scale, 0)
                pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY2), scale, 0)
                pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY3), scale, 0)
                pygame.display.flip()
                pygame.time.wait(2)
        if unittype == "weap":
            if deathname == "recall" and deathdisabled == False:
                self.client.moonaudio.sound("recall.ogg")   
            elif deathname == "repair" and deathdisabled == False:
                self.client.moonaudio.sound("repair.ogg")
            elif deathname == "virus" and deathdisabled == False:
                self.client.moonaudio.sound("virus.ogg")
            elif deathname == "spike" and deathdisabled == False:
                self.client.moonaudio.sound("spike.ogg")
            elif deathname == "emp" and deathdisabled == False:
                self.client.moonaudio.sound("emp.ogg")
                map_pos = deathX, deathY
                blitX, blitY = self.map_to_gui(map_pos)
                blitX = blitX + 24
                blitY = blitY + 24
                blitX2 = blitX + (self.map.xsize * self.tileset.tile_width)
                blitX3 = blitX - (self.map.xsize * self.tileset.tile_width)
                blitY2 = blitY + (self.map.ysize * self.tileset.tile_height)
                blitY3 = blitY - (self.map.ysize * self.tileset.tile_height)
                scale = 0
                while scale < (radius * 24):
                    scale = scale + 1
                    pygame.draw.circle(self.client.screen, (10, 75, 255), (blitX, blitY), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX2, blitY), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX3, blitY), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY2), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY3), scale, 0)
                    pygame.display.flip()
                    pygame.time.wait(2)
            elif deathname == "mines" and deathdisabled == False:
                self.client.moonaudio.sound("mediumboom.ogg")
                map_pos = deathX, deathY
                blitX, blitY = self.map_to_gui(map_pos)
                blitX = blitX + 12
                blitY = blitY + 12
                blitX2 = blitX + (self.map.xsize * self.tileset.tile_width)
                blitX3 = blitX - (self.map.xsize * self.tileset.tile_width)
                blitY2 = blitY + (self.map.ysize * self.tileset.tile_height)
                blitY3 = blitY - (self.map.ysize * self.tileset.tile_height)
                scale = 0
                while scale < (radius * 24):
                    scale = scale + 1
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX2, blitY), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX3, blitY), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY2), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY3), scale, 0)
                    pygame.display.flip()
                    pygame.time.wait(2)
            elif deathname == "crawler" and deathdisabled == False:
                self.client.moonaudio.sound("biggestboom.ogg")
                map_pos = deathX, deathY
                blitX, blitY = self.map_to_gui(map_pos)
                blitX = blitX + 24
                blitY = blitY + 24
                blitX2 = blitX + (self.map.xsize * self.tileset.tile_width)
                blitX3 = blitX - (self.map.xsize * self.tileset.tile_width)
                blitY2 = blitY + (self.map.ysize * self.tileset.tile_height)
                blitY3 = blitY - (self.map.ysize * self.tileset.tile_height)
                scale = 0
                while scale < (radius * 24):
                    scale = scale + 1
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX2, blitY), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX3, blitY), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY2), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY3), scale, 0)
                    pygame.display.flip()
                    pygame.time.wait(2)
            else:
                self.client.moonaudio.sound("mediumboom.ogg")
                map_pos = deathX, deathY
                blitX, blitY = self.map_to_gui(map_pos)
                blitX = blitX + 24
                blitY = blitY + 24
                blitX2 = blitX + (self.map.xsize * self.tileset.tile_width)
                blitX3 = blitX - (self.map.xsize * self.tileset.tile_width)
                blitY2 = blitY + (self.map.ysize * self.tileset.tile_height)
                blitY3 = blitY - (self.map.ysize * self.tileset.tile_height)
                scale = 0
                while scale < (radius * 24):
                    scale = scale + 1
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX2, blitY), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX3, blitY), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY2), scale, 0)
                    pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY3), scale, 0)
                    pygame.display.flip()
                    pygame.time.wait(2)

        if unittype == "tether":
            pop = random.randint(1, 6)
            if pop == 1:
                self.client.moonaudio.sound("tetherpop.ogg")
            if pop == 2:
                self.client.moonaudio.sound("tetherpop2.ogg")
            if pop == 3:
                self.client.moonaudio.sound("tetherpop3.ogg")
            if pop == 4:
                self.client.moonaudio.sound("tetherpop4.ogg")
            if pop == 5:
                self.client.moonaudio.sound("tetherpop5.ogg")
            if pop == 6:
                self.client.moonaudio.sound("tetherpop6.ogg")

            map_pos = deathX, deathY
            blitX, blitY = self.map_to_gui(map_pos)
            blitX = blitX + 12
            blitY = blitY + 12
            blitX2 = blitX + (self.map.xsize * self.tileset.tile_width)
            blitX3 = blitX - (self.map.xsize * self.tileset.tile_width)
            blitY2 = blitY + (self.map.ysize * self.tileset.tile_height)
            blitY3 = blitY - (self.map.ysize * self.tileset.tile_height)
            scale = 0
            while scale < (radius * 24):
                scale = scale + 1
                pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY), scale, 0)
                pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX2, blitY), scale, 0)
                pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX3, blitY), scale, 0)
                pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY2), scale, 0)
                pygame.draw.circle(self.client.screen, (255, 75, 10), (blitX, blitY3), scale, 0)
                pygame.display.flip()
                pygame.time.wait(2)
        if not self.client.deathtypes:
            self.client.dying_unit = False

