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
from twisted.spread import pb
from twisted.cred.portal import IRealm
import cPickle
import zlib

from conninfo import *


#****************************************************************************
#
#****************************************************************************
"""Code for handling both incoming and outgoing networks commands for the server, equivalent to networkclient.py for the client. Everything with 'perspective' in front of it is for commands coming in from a client."""
class ClientPerspective(pb.Avatar):
    def __init__(self, conn_info, conn_handler, serverstate):
        self.conn_info = conn_info
        self.state = serverstate
        self.handler = conn_handler

#****************************************************************************
# Todo: Add error handling.
#****************************************************************************
    def network_prepare(self, object):
        data = cPickle.dumps(object)
        compressed = zlib.compress(data)
        return compressed

#****************************************************************************
#
#****************************************************************************
    def network_handle(self, string):
        data = zlib.decompress(string)
        object = cPickle.loads(data)
        return object


#****************************************************************************
#client connects to game
#****************************************************************************
    def perspective_login(self, username, version):
        if version != self.state.settings.version:
            logging.warning("Server refused login due to version mismatch")
            return "login_failed"
        elif username == "server" or username == "Server": #the name 'server' is reserved for messages from the real server
            logging.warning("Server refused login due to invalid username")
            return "login_failed"
        else:                
            self.conn_info.username.append(username)
            newplayerID = self.state.max_players()
            newplayerID += 1
            self.conn_info.playerID.append(newplayerID)
            self.conn_info.teamID.append(newplayerID)
            self.state.playerIDs.append(newplayerID)
            self.state.teams.append(newplayerID)
            self.conn_info.reload.append(False)
            self.conn_info.undisable.append(False)
            self.conn_info.energy.append(11)
            self.conn_info.Idisabled.append([0])
            self.conn_info.Ireloading.append([0])
            server_message = "Server: %s has joined the game as player %s on team %s" % (username, str(newplayerID), str(newplayerID))
            self.handler.remote_all('chat', server_message)
            return newplayerID

#****************************************************************************
#client adds hotseat or bot player
#****************************************************************************
    def perspective_add_xplayer(self, username):
        self.conn_info.username.append(username)
        newplayerID = self.state.max_players()
        newplayerID += 1
        self.conn_info.playerID.append(newplayerID)
        self.conn_info.teamID.append(newplayerID)
        self.state.playerIDs.append(newplayerID)
        self.state.teams.append(newplayerID)
        self.conn_info.reload.append(False)
        self.conn_info.undisable.append(False)
        self.conn_info.energy.append(11)
        self.conn_info.Idisabled.append([0])
        self.conn_info.Ireloading.append([0])
        server_message = "Server: %s has joined the game as player %s on team %s" % (username, str(newplayerID), str(newplayerID))
        self.handler.remote_all('chat', server_message)
        self.handler.remote(self.conn_info.ref, "confirm_xplayer", newplayerID)

#****************************************************************************
#command to update pre-game settings
#****************************************************************************
    def perspective_update_pregame_settings(self, map_size, game_type):
        if self.conn_info.playerID[1] == 1: #player1 is the host and should be the only one allowed to change host settings               
            self.handler.remote_all("update_pregame_settings", map_size, game_type)
        else:
            self.handler.remote_all("cheat_signal", self.conn_info.playerID[1])
            logging.critical("PlayerID " + str(self.conn_info.playerID[1]) + " attempted to modify pregame settings")

#****************************************************************************
#command to update teams on server
#****************************************************************************
    def perspective_update_server_teams(self, playerID, teamID):
        playerID = int(playerID)
        teamID = int(teamID)
        if playerID > 0 and teamID > 0 and self.state.max_players() > 1:
            for checkplayer in self.state.playerIDs:
                if checkplayer == playerID:
                    self.state.teams[playerID] = teamID
                    logging.info("Player " + str(playerID) + " was moved to team " + str(teamID))
                    server_message = "Server: Host has moved player %s to team %s" % (str(playerID), str(teamID))
                    self.handler.remote_all('chat', server_message)
                    self.handler.remote_all("confirm_teams")
            server_message = "Server: Unable to move player %s, player not found" % (str(playerID))
        else:
            server_message = "Server: Invalid input for team change"
            self.handler.remote(self.conn_info.ref, 'chat', server_message)

#****************************************************************************
#client requesting individual teamID confirmation
#****************************************************************************
    def perspective_team_report(self, teamID):
        if self.state.teams[self.conn_info.playerID] != teamID:
            self.conn_info.teamID = self.state.teams[self.conn_info.playerID]
            self.handler.remote(self.conn_info.ref, "update_team", self.conn_info.teamID)
#****************************************************************************
#command that everyone is ready and the game actually starts
#****************************************************************************
    def perspective_init_game(self):
        count_teams = 0
        counting = 0
        enoughteams = False
        for count_teams in self.state.teams:
            if counting == 1:
                team1 = count_teams
                counting = 2
            elif counting != 0 and count_teams != team1:
                enoughteams = True
            elif counting == 0:
                counting = 1
        if enoughteams == False:
            server_message = "Server: All players are on the same team!"
            self.handler.remote_all('chat', server_message)
        elif self.state.runningserver == False:
            self.state.runningserver = True
            self.state.setup_new_game()
            net_map = self.network_prepare(self.state.map.mapstore) 
            net_unit_list = self.network_prepare(self.state.map.unitstore) 
            self.handler.remote_all('map', net_map)
            self.handler.remote_all('unit_list', net_unit_list)
            self.handler.remote_all('start_client_game')
            self.handler.remote_all('update_energy', 11, 0) #all players start with 11 energy, player 0 is specified to indicate this to server
            self.state.currentplayer = 1 #player1 goes first 
            self.handler.remote_all('next_turn', self.state.currentplayer)
            self.state.takingturn = False

#****************************************************************************
# recieve command for launching a unit, signifying a players turn is done
#****************************************************************************
    def perspective_launch_unit(self, parentID, unit, rotation, power, clientID):
        if self.state.endgame == True: #when game is over no actions are permitted
            return
        self.state.waitingclients = 0
        if self.conn_info.reload[clientID] == True: #reloading units remain disabled until the end of this turn
            logging.debug("reloading AA's")
            for loaded in self.conn_info.Ireloading[clientID]:
                for findloaded in self.state.map.unitstore.values():
                    if findloaded.id == loaded:
                        findloaded.reloading = False
                        findloaded.disabled = True
                        self.conn_info.Idisabled[clientID].append(findloaded.id)
                        self.conn_info.undisable[clientID] = True
        self.conn_info.reload[clientID] = False
        self.conn_info.Ireloading[clientID] = []

        nocheat = True #trying to detect cheating clients
        if self.conn_info.playerID[clientID] != self.state.currentplayer:
            self.handler.remote_all("cheat_signal", self.conn_info.playerID[clientID])
            logging.critical("PlayerID " + str(self.conn_info.playerID[clientID]) + " attempted to fire when it was player " + str(self.state.currentplayer) + " turn")
            nocheat = False
        if self.state.takingturn == True:
            self.handler.remote_all("cheat_signal", self.conn_info.playerID[clientID])
            logging.critical("PlayerID " + str(self.conn_info.playerID[clientID]) + " attempted to fire again after they had already fired")
            nocheat = False
        else:
            self.state.takingturn = True
        for checkcheat in self.state.map.unitstore.values():
            if checkcheat.id == parentID and (checkcheat.disabled == True or checkcheat.virused == True):
                self.handler.remote_all("cheat_signal", self.conn_info.playerID)
                logging.critical("PlayerID " + str(self.conn_info.playerID[clientID]) + " attempted to launch from disabled unit " + str(parentID))
                nocheat = False
            if checkcheat.id == parentID and checkcheat.type.id != "hub":
                if checkcheat.type.id != "offense":
                    self.handler.remote_all("cheat_signal", self.conn_info.playerID[clientID])
                    logging.critical("PlayerID " + str(self.conn_info.playerID[clientID]) + " attempted to launch from a " + str(checkcheat.type.id))
                    nocheat = False
                elif unit == "repair" or self.state.game.get_unit_typeset(unit) != "weap":
                    self.handler.remote_all("cheat_signal", self.conn_info.playerID[clientID])
                    logging.critical("PlayerID " + str(self.conn_info.playerID[clientID]) + " attempted to launch a " + str(unit) + " from an " + str(checkcheat.type.id))
                    nocheat = False
        if self.conn_info.energy[clientID] < self.state.game.get_unit_cost(unit): 
            self.handler.remote_all("cheat_signal", self.conn_info.playerID[clientID])
            logging.critical("PlayerID " + str(self.conn_info.playerID[clientID]) + " attempted to use " + str(self.state.game.get_unit_cost(unit)) + " energy when server reports only having " + str(self.conn_info.energy[clientID] + " energy!"))
            nocheat = False
        for player in self.state.deadplayers:
            if player == self.conn_info.playerID[clientID]:
                self.handler.remote_all("cheat_signal", self.conn_info.playerID[clientID])
                logging.critical("PlayerID " + str(self.conn_info.playerID[clientID]) + " attempted to take a turn after dying")
                nocheat = False

        if nocheat == True:
            if unit == "mines" or unit == "cluster": #handling 'split' shots
                (startx, starty, coord1X, coord1Y, coord2X, coord2Y, coord3X, coord3Y, disabled1, disabled2, disabled3) = self.state.split_trajectory(parentID, rotation, power, unit, self.conn_info, clientID)
                coord1X = int(coord1X)
                coord1Y = int(coord1Y)
                coord2X = int(coord2X)
                coord2Y = int(coord2Y)
                coord3X = int(coord3X)
                coord3Y = int(coord3Y)
                coord1 = (coord1X, coord1Y)
                coord2 = (coord2X, coord2Y)
                coord3 = (coord3X, coord3Y)
                self.state.deathlist = []
                if self.conn_info.undisable[clientID] == True: #undisabling units caused by this player previously
                    logging.info("undisabling units")
                    for undisable in self.conn_info.Idisabled[clientID]:
                        for finddisabled in self.state.map.unitstore.values():
                            if finddisabled.id == undisable :
                                finddisabled.disabled = False
                                logging.debug("undisabled a " + str(finddisabled.type.id))
                self.conn_info.undisable[clientID] = False
                self.conn_info.Idisabled[clientID] = []
                self.conn_info.energy[clientID] = self.conn_info.energy[clientID] - self.state.game.get_unit_cost(unit)
                self.handler.remote(self.conn_info.ref, "update_energy", self.conn_info.energy[clientID], self.conn_info.playerID[clientID])
                collecting = False

                self.state.game.create_unit(unit, coord1, self.conn_info.playerID[clientID], parentID, collecting, rotation, self.state.teams[self.conn_info.playerID[clientID]])
                if disabled1 == False:
                    self.state.determine_hit(unit, coord1, self.conn_info, clientID)
                self.state.game.create_unit(unit, coord2, self.conn_info.playerID[clientID], parentID, collecting, rotation, self.state.teams[self.conn_info.playerID[clientID]])
                if disabled2 == False:
                    self.state.determine_hit(unit, coord2, self.conn_info, clientID)
                self.state.game.create_unit(unit, coord3, self.conn_info.playerID[clientID], parentID, collecting, rotation, self.state.teams[self.conn_info.playerID[clientID]])
                if disabled3 == False:
                    self.state.determine_hit(unit, coord3, self.conn_info, clientID)

                logging.info("added " + unit + " at: " + str(coord1X) + ", " + str(coord1Y))
                logging.info("added " + unit + " at: " + str(coord2X) + ", " + str(coord2Y))
                logging.info("added " + unit + " at: " + str(coord3X) + ", " + str(coord3Y))
                self.handler.remote_all('show_launch', startx, starty, rotation, power, unit, self.conn_info.playerID[clientID])

            else: #handling normal shots
                (startx, starty, coordX, coordY, collecting) = self.state.find_trajectory(parentID, rotation, power, unit, self.conn_info, clientID)
                coord = (coordX, coordY)
                self.state.deathlist = []
                if self.conn_info.undisable[clientID] == True: #undisabling units caused by this player previously
                    logging.info("undisabling units")
                    for undisable in self.conn_info.Idisabled[clientID]:
                        for finddisabled in self.state.map.unitstore.values():
                            if finddisabled.id == undisable:
                                finddisabled.disabled = False
                                logging.debug("undisabled a " + str(finddisabled.type.id))
                self.conn_info.undisable[clientID] = False
                self.conn_info.Idisabled[clientID] = []
                self.conn_info.energy[clientID] = self.conn_info.energy[clientID] - self.state.game.get_unit_cost(unit)
                self.handler.remote(self.conn_info.ref, "update_energy", self.conn_info.energy[clientID], self.conn_info.playerID[clientID])
                    
                if self.state.doubletether == False:
                    self.state.game.create_unit(unit, coord, self.conn_info.playerID[clientID], parentID, collecting, rotation, self.state.teams[self.conn_info.playerID[clientID]])
                else:
                    self.state.game.tether2unit(unit, coord, self.conn_info.playerID[clientID], parentID, collecting, rotation, self.state.teams[self.conn_info.playerID[clientID]])

                if self.state.interrupted_tether == True:
                    victim = self.state.map.get_unit_from_id(self.state.game.unit_counter)
                    victim.disabled = True
                    victim.hp = 0

                logging.info("added " + unit + " at: " + str(coordX) + ", " + str(coordY) + "; for playerID " + str(self.conn_info.playerID[clientID]))
                if self.state.game.get_unit_typeset(unit) == "weap":
                    self.state.determine_hit(unit, coord, self.conn_info, clientID)
                elif collecting == True:
                    self.handler.remote(self.conn_info.ref, "collecting_energy")
                self.handler.remote_all('show_launch', startx, starty, rotation, power, unit, self.conn_info.playerID[clientID])

        else: #cheaters miss their turn but no other penalty
            self.state.detonate_waiters()
            self.eliminate_players()
            net_map = self.network_prepare(self.state.map.mapstore) 
            net_unit_list = self.network_prepare(self.state.map.unitstore) 
            self.handler.remote_all("map", net_map)
            self.handler.remote_all("unit_list", net_unit_list)
            foundplayer = False
            while not foundplayer:
                self.state.currentplayer += 1
                if self.state.currentplayer > self.state.max_players():
                    logging.info("max players = %s" % self.state.max_players())
                    self.state.currentplayer = 0
                if len(self.state.skippedplayers) > 1:
                    for search in self.state.skippedplayers:
                        logging.debug("searching found skipped player# %s" % search)
                        logging.debug("currentplayer = %s" % self.state.currentplayer)
                        if search != 0:
                            if int(search) != self.state.currentplayer and self.state.currentplayer > 0:
                                logging.debug("found searching found %s" % search)
                                logging.info("currentplayer = %s" % self.state.currentplayer)
                                foundplayer = True
                else:
                    logging.debug("no skips yet")
                    if self.state.currentplayer == 0:
                        self.state.currentplayer = 1
                    foundplayer = True
                    logging.info("currentplayer = %s" % self.state.currentplayer)

            self.handler.remote_all('next_turn', self.state.currentplayer)
            self.state.takingturn = False
            

#****************************************************************************
#recieve command indicating that this player is skipping all turns until round is over
#****************************************************************************
    def perspective_skip_round(self, clientID):
        if self.state.endgame == True: #when game is over no actions are permitted
            return

        nocheat = True #trying to detect cheating clients
        if self.conn_info.playerID[clientID] != self.state.currentplayer:
            self.handler.remote_all("cheat_signal", self.conn_info.playerID[clientID])
            logging.critical("PlayerID " + str(self.conn_info.playerID[clientID]) + " attempted to fire when it was player " + str(self.state.currentplayer) + " turn")
            nocheat = False
        if self.state.takingturn == True:
            self.handler.remote_all("cheat_signal", self.conn_info.playerID[clientID])
            logging.critical("PlayerID " + str(self.conn_info.playerID[clientID]) + " attempted to fire again after they had already fired")
            nocheat = False
        else:
            self.state.takingturn = True

        for player in self.state.deadplayers:
            if player == self.conn_info.playerID[clientID]:
                self.handler.remote_all("cheat_signal", self.conn_info.playerID[clientID])
                logging.critical("PlayerID " + str(self.conn_info.playerID[clientID]) + " attempted to take a turn after dying")
                nocheat = False

        if nocheat == True:
            self.state.skippedplayers.append(self.conn_info.playerID[clientID])
            #this is different from OMBC, here energy collection is performed when the player skips, not when the round actually ends. This is because of a problem with the server that prevents me from sending messages to a specific user unless that user sent the command to the server that started the function
            self.state.detonate_waiters()
            self.eliminate_players()
            self.conn_info.energy[clientID] = self.state.calculate_energy(self.conn_info.playerID[clientID], self.conn_info.energy[clientID])
            self.handler.remote(self.conn_info.ref, 'update_energy', self.conn_info.energy[clientID], self.conn_info.playerID[clientID])
            if self.conn_info.undisable[clientID] == True: #undisabling units caused by this player previously
                logging.info("undisabling units")
                for undisable in self.conn_info.Idisabled[clientID]:
                    for finddisabled in self.state.map.unitstore.values():
                        if finddisabled.id == undisable:
                            finddisabled.disabled = False
            self.conn_info.undisable[clientID] = False
            self.conn_info.Idisabled[clientID] = []
            if len(self.state.skippedplayers) > self.state.max_players(): #don't forget, player0 is always skipped to avoid having a blank list so there is always 1 more skipped players then actually exist
                self.state.skippedplayers = []
                for player in self.state.deadplayers:
                    self.state.skippedplayers.append(player) #skipping dead players
                self.state.move_crawlers()
                self.handler.remote_all('next_round')
                self.state.roundplayer += 1
                if self.state.roundplayer > self.state.max_players():
                    self.state.roundplayer = 1
                self.state.currentplayer = self.state.roundplayer - 1 #remember currentplayer will be incremented soon
            foundplayer = False
            while not foundplayer:
                self.state.currentplayer += 1
                if self.state.currentplayer > self.state.max_players():
                    self.state.currentplayer = 0
                if len(self.state.skippedplayers) > 1:
                    for search in self.state.skippedplayers:
                        logging.debug("searching found skipped player# %s" % search)
                        logging.debug("currentplayer = %s" % self.state.currentplayer)
                        if search != 0:
                            if int(search) != self.state.currentplayer and self.state.currentplayer > 0:
                                logging.debug("found searching found %s" % search)
                                logging.debug("currentplayer = %s" % self.state.currentplayer)
                                foundplayer = True
                else:
                    logging.debug("no skips yet")
                    if self.state.currentplayer == 0:
                        self.state.currentplayer = 1
                    foundplayer = True
                    logging.info("currentplayer = %s" % self.state.currentplayer)


            self.state.detonate_waiters()
            self.eliminate_players()
            net_map = self.network_prepare(self.state.map.mapstore) 
            net_unit_list = self.network_prepare(self.state.map.unitstore) 
            self.handler.remote_all("map", net_map)
            self.handler.remote_all("unit_list", net_unit_list)
            self.handler.remote_all('next_turn', self.state.currentplayer)
            self.state.takingturn = False
            if self.state.endgame == True:
                self.handler.remote_all("endgame")
            self.state.game.unit_dump()

#****************************************************************************
#after all clients reports it has completed animation server sends updated map and process death
#****************************************************************************
    def perspective_unit_landed(self):
        self.state.waitingclients += 1
        if self.state.waitingclients == self.state.max_clients(self.handler.clients):
            self.state.waitingclients = 0
            self.state.detonate_waiters()
            self.eliminate_players()
            net_map = self.network_prepare(self.state.map.mapstore) 
            net_unit_list = self.network_prepare(self.state.map.unitstore) 
            self.handler.remote_all("map", net_map)
            self.handler.remote_all("unit_list", net_unit_list)
            foundplayer = False
            while not foundplayer:
                self.state.currentplayer += 1
                if self.state.currentplayer > self.state.max_players():
                    self.state.currentplayer = 0
                if len(self.state.skippedplayers) > 1:
                    for search in self.state.skippedplayers:
                        logging.debug("searching found skipped player# %s" % search)
                        logging.debug("currentplayer = %s" % self.state.currentplayer)
                        if search != 0:
                            if int(search) != self.state.currentplayer and self.state.currentplayer > 0:
                                logging.debug("found searching found %s" % search)
                                logging.debug("currentplayer = %s" % self.state.currentplayer)
                                foundplayer = True
                else:
                    logging.debug("no skips yet")
                    if self.state.currentplayer == 0:
                        self.state.currentplayer = 1
                    foundplayer = True
                    logging.info("currentplayer = %s" % self.state.currentplayer)
                    
            self.handler.remote_all('next_turn', self.state.currentplayer)
            self.state.takingturn = False
            if self.state.endgame == True:
                self.handler.remote_all("endgame")

#****************************************************************************
#forward chat information to all clients
#****************************************************************************
    def perspective_send_chat(self, data):
        message = str(self.conn_info.username[1]) + ": " + self.network_handle(data)
        if self.state.runningserver == False:
            self.handler.remote_all('chat', message)
        elif len(message) < 82:
            self.handler.remote_all('chat', message)
        else:
            self.handler.remote(self.conn_info.ref, 'chat', "Server: your message was too long to display, message not sent")

#****************************************************************************
#client disconnecting from server completely
#****************************************************************************
    def logout(self):
        logging.info("logged out")
        clientID = 0
        print"server ran logout function"
        del self.handler.clients[self.conn_info.ref]
        for clients in self.conn_info.playerID:
            if self.conn_info.playerID[clientID] > 0:
                server_message = "Server: Player %s has left the game" % str(self.conn_info.playerID[clientID])
                self.handler.remote_all('chat', server_message)
                if self.conn_info.playerID[clientID] == 1:
                    server_message = "Server: Host has left the game"
                    self.state.endgame = True
                    self.handler.remote_all("endgame")
                if self.state.endgame == False and self.state.runningserver == True:
                    for unit in self.state.map.unitstore.values():
                        if unit.playerID == self.conn_info.playerID[clientID]:
                            unit.hp = 0
                    self.state.detonate_waiters()
                    self.eliminate_players()
                    net_map = self.network_prepare(self.state.map.mapstore) 
                    net_unit_list = self.network_prepare(self.state.map.unitstore) 
                    self.handler.remote_all("map", net_map)
                    self.handler.remote_all("unit_list", net_unit_list)
                if self.state.endgame == False: #this is intentional as endgame state may have changed
                    if self.state.currentplayer == self.conn_info.playerID[clientID]:
                        foundplayer = False
                        while not foundplayer:
                            self.state.currentplayer += 1
                            if self.state.currentplayer > self.state.max_players():
                                self.state.currentplayer = 0
                            if len(self.state.skippedplayers) > 1:
                                for search in self.state.skippedplayers:
                                    logging.debug("searching found skipped player# %s" % search)
                                    logging.debug("currentplayer = %s" % self.state.currentplayer)
                                    if search != 0:
                                        if int(search) != self.state.currentplayer and self.state.currentplayer > 0:
                                            logging.debug("found searching found %s" % search)
                                            logging.debug("currentplayer = %s" % self.state.currentplayer)
                                            foundplayer = True
                            else:
                                logging.debug("no skips yet")
                                if self.state.currentplayer == 0:
                                    self.state.currentplayer = 1
                                foundplayer = True
                                logging.info("currentplayer = %s" % self.state.currentplayer)
                                
                        self.handler.remote_all('next_turn', self.state.currentplayer)
                        self.state.takingturn = False
                else:
                    self.handler.remote_all("endgame")
            clientID += 1

#****************************************************************************
#host shutting down
#****************************************************************************
    def perspective_hostquit(self):
        if self.conn_info.playerID[1] == 1: #player1 is the host and should be the only one allowed to change host settings               
            self.handler.remote_all("server_shutdown")
        else:
            self.handler.remote_all("cheat_signal", self.conn_info.playerID[1])
            logging.critical("PlayerID " + str(self.conn_info.playerID[1]) + " attempted to force server shutdown")


#****************************************************************************
#calculate the number of players currently connected to the game
#****************************************************************************
    def eliminate_players(self):
        for playerID in self.state.playerIDs:
            isdead = True
            unskipped = True
            notdead = True
            if self.state.endgame == False:
                for unit in self.state.map.unitstore.values():
                    if unit.playerID == playerID and unit.type.id == "hub":
                        isdead = False #player is proven alive if they have at least one hub
                if isdead == True:
                    for findskipped in self.state.skippedplayers: #skipping dead player if not pre-skipped
                        if findskipped == playerID:
                            unskipped = False
                    for finddead in self.state.deadplayers:
                        if finddead == playerID:
                            notdead = False
                    if unskipped == True:
                        self.state.skippedplayers.append(playerID)
                    if notdead == True: #player is now dead but wasn't dead before this moment
                        self.state.deadplayers.append(playerID)
                        logging.info("player " + str(playerID) + " has been eliminated")
                        self.state.teams[playerID] = 0 #removing dead player from team list
                    teamwin = True
                    self.state.teams[playerID] = 0 #removing dead player from team list
                    for checkteam in self.state.teams:
                        if checkteam > 0:
                            for doublecheckteam in self.state.teams:
                                if doublecheckteam > 0 and doublecheckteam != checkteam:
                                    teamwin = False #at least 2 different teams still have players so game continues
                    if teamwin == True:
                        logging.info("game is over")
                        self.state.endgame = True
                        self.handler.remote_all("endgame")                            
                    logging.debug("Player " + str(playerID) + " is still dead")

#****************************************************************************
#
#****************************************************************************
class ConnectionHandler:
    __implements__ = IRealm

    def __init__(self, serverstate):
        self.state = serverstate
        self.clients = {}

#****************************************************************************
#send data to all clients
#****************************************************************************
    def remote_all(self, methodName, *args):
        dfs = [self.remote(c, methodName, *args) for c in self.clients]
        return dfs 

#****************************************************************************
#send data to a single client
#****************************************************************************
    def remote(self, client, method_name, *args):
        return client.callRemote(method_name, *args)

#****************************************************************************
#server information about each player
#****************************************************************************
    def requestAvatar(self, name, client_ref, *interfaces):
        logging.info("Client connected.")
        if pb.IPerspective in interfaces:
            address = client_ref.broker.transport.getPeer()
            playerID = []
            energy = []
            undisable = []
            Idisabled = []
            reload = []
            Ireloading = []
            conn_info = ConnInfo(client_ref, name, address, playerID, energy, Idisabled, reload, Ireloading)
            perspective = ClientPerspective(conn_info, self, self.state)
            self.clients[client_ref] = conn_info
            return (pb.IPerspective, perspective, perspective.logout) 
        else:
            raise NotImplementedError("no interface")


