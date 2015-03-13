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
import logging
from twisted.internet import reactor
from twisted.spread import pb
from twisted.cred.credentials import UsernamePassword
import cPickle
import zlib
import time
import subprocess

#****************************************************************************
#
#****************************************************************************
"""Code for handling both incoming and outgoing networks commands for the client, equivalent to connectionhandler.py for the server. Everything with 'remote' in front of it is an incoming command from the server."""
class NetworkClient(pb.Referenceable):
    def __init__(self, clientstate):
        self.perspective = None
        self.client = clientstate

#****************************************************************************
# Todo: Add error handling
#****************************************************************************
    def network_handle(self, string):
        data = zlib.decompress(string)
        object = cPickle.loads(data)
        return object

#****************************************************************************
#
#****************************************************************************
    def network_prepare(self, object):
        data = cPickle.dumps(object)
        compressed = zlib.compress(data)
        return compressed


#****************************************************************************
# connect to server
#****************************************************************************
    def connect(self, server, serverPort, username):
        self.server = server
        self.serverPort = serverPort
        self.username = username
        self.factory = pb.PBClientFactory()
        self.client_connection = reactor.connectTCP(server, 6112, self.factory)
        self.df = self.factory.login(UsernamePassword("guest", "guest"), self)
        self.df.addCallback(self.connected)
        if reactor.running == False:
            reactor.run()

#****************************************************************************
# add hotseat or bot player
#****************************************************************************
    def add_xplayer(self, AIlevel):
        if AIlevel == 0:
            self.client.AItype.append(AIlevel)
            username = "Hotseat"
            self.perspective.callRemote('add_xplayer', username)
        elif AIlevel == 1:
            self.client.AItype.append(AIlevel)
            username = "Dumb-bot"
            self.perspective.callRemote('add_xplayer', username)
        else:
            self.client.moonaudio.narrate("disabled.ogg")

#****************************************************************************
# update pregame setup
#****************************************************************************
    def update_pregame_settings(self, map_size, game_type):
        self.perspective.callRemote('update_pregame_settings', map_size, game_type)

#****************************************************************************
# update team settings
#****************************************************************************
    def update_server_teams(self, playerID, teamID):
        self.perspective.callRemote('update_server_teams', playerID, teamID)

#****************************************************************************
# command for server to setup game
#****************************************************************************    
    def start_server_game(self):
        self.perspective.callRemote('init_game')

#****************************************************************************
# command to actually fire something
#****************************************************************************
    def launch_unit(self, parentID, unit, rotation, power):
        self.client.myturn == False
        self.client.launching_unit[self.client.clientID] = parentID
        self.perspective.callRemote('launch_unit', parentID, unit, rotation, power, self.client.clientID)

#****************************************************************************
# report completion of animation by client
#****************************************************************************
    def land_unit(self):
        self.perspective.callRemote('unit_landed')

#****************************************************************************
# command that player is 'skipping' this turn
#****************************************************************************
#After being run once this should be run every time this clients turn comes around until server reports that the entire round is over."""
    def skip_round(self):
        self.perspective.callRemote('skip_round', self.client.clientID)

#****************************************************************************
# 
#****************************************************************************
    def success(self, message):
        logging.debug("Message received: %s" % message)

#****************************************************************************
# 
#****************************************************************************
    def failure(self, error):
        logging.critical("error received from server:")
        reactor.stop()

#****************************************************************************
# 
#****************************************************************************
    def connected(self, perspective):
        self.perspective = perspective
        perspective.callRemote('login', self.username, self.client.settings.version).addCallback(self.login_result)
        
        logging.debug("connected.")

#****************************************************************************
# host attempting to report server shutdown
#****************************************************************************
    def hostquit(self):
        self.perspective.callRemote('hostquit')

#****************************************************************************
# recieve login information from server
#****************************************************************************
    def login_result(self, result):
        if result == "login_failed":
            logging.debug("Server denied login")
        else:
            self.client.playerID.append(result)
            self.client.teamID.append(result)
            self.client.energy.append(11)
            self.client.rotate_position.append(360)
            self.client.AItype.append(0)
            self.client.selected_weap.append("hub")
            self.client.launching_unit.append(0)
            logging.debug("Server accepted login")
            logging.debug("Your playerID = %r" % result)
            self.client.enter_pregame()
            message = "Server: Welcome player %s" % result
            self.client.pregame.show_message(message)

#****************************************************************************
# recieve xplayer login information from server
#****************************************************************************
    def remote_confirm_xplayer(self, result):
        self.client.playerID.append(result)
        self.client.teamID.append(result)
        self.client.energy.append(11)
        self.client.rotate_position.append(360)
        self.client.AItype.append(0)
        self.client.selected_weap.append("hub")
        self.client.launching_unit.append(0)
        logging.debug("Added XplayerID = %r" % result)      



#****************************************************************************
# recieve command that server is going down
#****************************************************************************
    def remote_server_shutdown(self):
        logging.info("Server reported shutdown")
        message = "Server: Host is leaving the game"
        if self.client.mappanel:
            self.client.mappanel.show_message(message)
        if self.client.pregame:
            self.client.pregame.show_message(message)
        time.sleep(2)
        if self.client.debug == True:
            subprocess.Popen(["./moon.py", "--no-intro", "--debug"])
        else:
            subprocess.Popen(["./moon.py", "--no-intro"])
        self.client.quit()
        

#****************************************************************************
# send chat information
#****************************************************************************
    def send_chat(self, message):
        data = self.network_prepare(message)
        self.perspective.callRemote('send_chat', data)


    def error(self, failure, op=""):
        logging.critical('Error in %s: %s' % (op, str(failure.getErrorMessage())))
        if reactor.running:
            reactor.stop()


# Methods starting with remote_ can be called by the server. (basically incoming message)
    def remote_chat(self, message):
        if self.client.mappanel:
            self.client.mappanel.show_message(message)
        if self.client.pregame:
            self.client.pregame.show_message(message)

    def remote_network_sync(self):
        logging.debug("* Network sync")
        self.client.game_next_phase()


#****************************************************************************
# recieve updated unit information
#****************************************************************************
    def remote_unit_list(self, net_unit_list):
        self.client.map.unitstore = self.network_handle(net_unit_list)
        for unit in self.client.map.unitstore.values(): #update selected unit with updated information
            for unit2 in self.client.selected_unit.values():
                if unit.id == unit2.id:
                    map_pos = (unit.x, unit.y)
                    self.client.selected_unit = {}
                    self.client.selected_unit.update({map_pos:unit})
        self.client.updated_map = True

#****************************************************************************
# recieve updated map information
#****************************************************************************
    def remote_map(self, net_map):
        self.client.map.mapstore = self.network_handle(net_map)

#****************************************************************************
# command that server is ready for clients to begin playing
#****************************************************************************
    def remote_start_client_game(self):
        self.client.moonaudio.narrate("launching_game.ogg")
        self.client.pregame.start_game()

#****************************************************************************
# recieve launch data from server
#****************************************************************************
    def remote_show_launch(self, startx, starty, rotation, power, unit, pID):
        self.client.deathtypes = []
        self.client.deathX = []
        self.client.deathY = []
        self.client.launch_startx = startx
        self.client.launch_starty = starty
        self.client.launch_direction = rotation
        self.client.launch_distance = power + 6
        self.client.launch_type = unit
        self.client.playerlaunched = pID
        self.client.launched = True
        self.client.moonaudio.sound("throw.ogg")
        self.client.missilelock = False
        self.client.hit1 = False
        self.client.hit2 = False
        self.client.hit3 = False
        if self.client.game.check_tether(unit) == True:
                if power < 9:
                    self.client.moonaudio.sound("shorttether.ogg")
                elif power > 8 and power < 17:
                    self.client.moonaudio.sound("mediumtether.ogg")
                elif power > 16:
                    self.client.moonaudio.sound("longtether.ogg")

#****************************************************************************
# recieve defense data from server
#****************************************************************************
    def remote_triggered_defense(self, defX, defY, tarX, tarY, targetnumb):
        logging.debug("defense triggered")
        if targetnumb == 1:
            self.client.defX = defX
            self.client.defY = defY
            self.client.tarX = tarX
            self.client.tarY = tarY
            self.client.intercepted = True
            self.client.hit1 = False
        if targetnumb == 2:
            self.client.defX2 = defX
            self.client.defY2 = defY
            self.client.tarX2 = tarX
            self.client.tarY2 = tarY
            self.client.intercepted2 = True
            self.client.hit2 = False
        if targetnumb == 3:
            self.client.defX3 = defX
            self.client.defY3 = defY
            self.client.tarX3 = tarX
            self.client.tarY3 = tarY
            self.client.intercepted3 = True
            self.client.hit3 = False

#****************************************************************************
# recieve unit death data from server
#****************************************************************************
    def remote_kill_unit(self, x, y, unittype, playerID, name, disabled):
        self.client.dying_unit = True
        self.client.deathtypes.append(unittype)
        self.client.deathX.append(x)
        self.client.deathY.append(y)
        self.client.deathplayerID.append(playerID)
        self.client.deathname.append(name)
        self.client.deathdisabled.append(disabled)

#****************************************************************************
# get energy from server
#****************************************************************************
    def remote_update_energy(self, energy, playerID):
        if playerID == 0: #playerID 0 is used here to tell client this is for all players
            count = 0
            for q in self.client.energy:
                if count > 0:
                    self.client.energy[count] = energy
                count += 1
        else:
            clientID = self.client.get_clientID(playerID)
            self.client.energy[clientID] = energy
            if self.client.energy[clientID] < self.client.game.get_unit_cost(self.client.selected_weap):
                self.client.selected_weap = "bomb" #game automatically switches to bomb when energy gets low

#****************************************************************************
# recieve command to restore energy and begin a new round
#****************************************************************************
    def remote_next_round(self):
        message = "Server: round over"
        self.client.mappanel.show_message(message)
        self.client.moonaudio.narrate("round_over.ogg")

#****************************************************************************
# notice of possible cheating by server
#****************************************************************************
    def remote_cheat_signal(self, playerID):
        self.client.moonaudio.narrate("cheat.ogg")
        message = "Server: Player ", str(playerID), " tried to cheat"
        if self.client.mappanel:
            self.client.mappanel.show_message(message)
        if self.client.pregame:
            self.client.pregame.show_message(message)

#****************************************************************************
# server detects something landing in water
#****************************************************************************
    def remote_splash(self):
        self.client.moonaudio.sound("watersplash.ogg")
        self.client.splashed = True

#****************************************************************************
# server detects a building landing on a rock
#****************************************************************************
    def remote_hit_rock(self):
        self.client.hit_rock = True

#****************************************************************************
# server detects collector landing on an energy pool
#****************************************************************************
    def remote_collecting_energy(self):
        self.client.collecting_energy = True

#****************************************************************************
# server has ended the game
#****************************************************************************
    def remote_endgame(self):
        self.client.moonaudio.narrate("winner.ogg")
        message = "Server: Game Over"
        if self.client.mappanel:
            self.client.mappanel.show_message(message)
        if self.client.pregame:
            self.client.pregame.show_message(message)

#****************************************************************************
# recieve command identifying which players turn it is
#****************************************************************************
    def remote_next_turn(self, next_player):
        checkID = self.client.get_clientID(next_player)
        if checkID == False:
            message = "Server: It is player " + str(next_player) + "'s turn"
            self.client.mappanel.show_message(message)
            self.client.myturn = False
        else:
            self.client.clientID = checkID
            if self.client.energy[self.client.clientID] < 1: #all players skip if no energy
                self.skip_round()
            elif self.client.AItype[self.client.clientID] == 0: #human players
                message = "Server: It's your turn commander"
                if self.client.mappanel:
                    self.client.mappanel.show_message(message)
                elif self.client.pregame:
                    self.client.pregame.show_message(message)
                else:
                    logging.critical("unable to find panel for displaying message")
                self.client.myturn = True
                self.client.firepower = 0
                self.client.power_direction = "up"
                self.client.moonaudio.narrate("your_turn.ogg")
                self.client.selected_unit = {}
                for unit in self.client.map.unitstore.values():
                    if unit.playerID == self.client.playerID[self.client.clientID] and unit.id == self.client.launching_unit[self.client.clientID]:
                        map_pos = (unit.x, unit.y)
                        self.client.selected_unit = {}
                        self.client.selected_unit.update({map_pos:unit})
            else: #bots
                message = "Server: It is player " + str(next_player) + "'s turn"
                self.client.mappanel.show_message(message)
                self.client.myturn = False
                (parentID, unit, rotation, power, skip) = self.client.AI.runbot(self.client.AItype[self.client.clientID])
                if skip == True:
                    self.skip_round()
                else:
                    self.perspective.callRemote('launch_unit', parentID, unit, rotation, power, self.client.clientID)
        logging.debug("It is player " + str(next_player) + "'s turn")

#****************************************************************************
# getting server map settings
#****************************************************************************
    def remote_resize_map(self, mapX, mapY):
        self.client.map.xsize = mapX
        self.client.map.ysize = mapY

#****************************************************************************
# getting pre-game settings
#****************************************************************************
    def remote_update_pregame_settings(self, map_size, game_type):
        self.client.pregame_mapsize = map_size
        self.client.game_type = game_type

#****************************************************************************
# server needing team update confirmation
#****************************************************************************
    def remote_confirm_teams(self):
        self.perspective.callRemote('team_report', self.client.teamID)

#****************************************************************************
# server overriding client team settings
#****************************************************************************
    def remote_update_team(self, teamID):
        self.client.teamID = teamID
