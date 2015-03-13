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

import sys, os

import pygame
from pygame.locals import *
import gui
import gettext
from random import *

from networkscreen import *
from universe import *

import tileset

from settingscreen import *

#****************************************************************************
# The MainMenu class shows buttons with choices for what game-mode
# which will be used.
#****************************************************************************
class MainMenu:
    def __init__(self, client):


        self.client = client

        if (self.client.settings.fullscreen):
            screen_mode = pygame.FULLSCREEN
        else:
            screen_mode = 0
        screen_width = self.client.settings.screen_width 
        screen_height = self.client.settings.screen_height 
        screen = pygame.display.set_mode((screen_width, screen_height), screen_mode)
        pygame.display.set_caption("MoonPy %s" % (self.client.settings.string_version))
        self.client.screen = screen

        self.app = gui.Desktop()
        self.app.connect(gui.QUIT, self.app.quit, None)
        container = gui.Container(align=-1, valign=-1)

        menu_table = gui.Table(width=200,height=220)
        network_start_button = gui.Button(("Start Multiplayer Game"))
        network_start_button.connect(gui.CLICK, self.network_start, None)
        menu_table.add(network_start_button, 0, 0)
        menu_table.add(gui.Widget(width=1, height=5), 0, 1)

        network_join_button = gui.Button(("Join Multiplayer Game"))
        network_join_button.connect(gui.CLICK, self.network_join, None)
        menu_table.add(network_join_button, 0, 2)
        menu_table.add(gui.Widget(width=1, height=5), 0, 3)

        network_online_button = gui.Button(("Find Online Game"))
        network_online_button.connect(gui.CLICK, self.network_online, None)
        menu_table.add(network_online_button, 0, 4)
        menu_table.add(gui.Widget(width=1, height=5), 0, 5)

        settings_button = gui.Button(("Settings"))
        settings_button.connect(gui.CLICK, self.settings_menu, None)
        menu_table.add(settings_button, 0, 6)
        menu_table.add(gui.Widget(width=1, height=5), 0, 7)

        """credits_button = gui.Button(("Credits"))
        credits_button.connect(gui.CLICK, self.credits_screen, None)
        menu_table.add(credits_button, 0, 8)
        menu_table.add(gui.Widget(width=1, height=5), 0, 9)"""

        quit_button = gui.Button(("Quit"))
        quit_button.connect(gui.CLICK, self.client.quit)
        menu_table.add(quit_button, 0, 8)

        intro_label = gui.Label(("Welcome to MoonPy"))

        container.add(MenuBackground(client=self.client, width = self.client.screen.get_width(),height = self.client.screen.get_height()), 0, 0)
        container.add(menu_table, self.client.screen.get_width() / 2 - 100, self.client.screen.get_height() / 2 - 100)
        container.add(intro_label, self.client.screen.get_width() / 2 - 65, self.client.screen.get_height() * 0.315)

        self.app.run(container)


#****************************************************************************
#  Start a network game.
#****************************************************************************
    def network_start(self, obj):
        self.client.moonaudio.sound("buttonclick.ogg")
        self.app.quit()
        ns = NetworkScreen(self.client)
        ns.start()

#****************************************************************************
#  Join a network game.
#****************************************************************************
    def network_join(self, obj):
        self.client.moonaudio.sound("buttonclick.ogg")
        self.app.quit()
        ns = NetworkScreen(self.client)
        ns.join()

#****************************************************************************
#  Find an online game.
#****************************************************************************
    def network_online(self, obj):
        self.client.moonaudio.sound("buttonclick.ogg")
        self.app.quit()
        un = Universe(self.client)
        un.connectIRC()
 
#****************************************************************************
#   Access the settings menu
#****************************************************************************
    def settings_menu(self, obj):
        self.client.moonaudio.sound("buttonclick.ogg")
        self.app.quit()
        ss = SettingsScreen(self.client)
        ss.settings_menu()

#****************************************************************************
#   Access the credits
#****************************************************************************
    def credits_screen(self, obj):
        self.client.moonaudio.narrate("disabled.ogg")

#****************************************************************************
#
#****************************************************************************
class ErrorMenu:
    def __init__(self, client, error_message):

        self.client = client
        self.app = gui.Desktop()
        self.app.connect(gui.QUIT, sys.exit, None)

        menu_table = gui.Table(width=200,height=120)
        error_label = gui.Label(error_message)
        menu_table.add(error_label, 0, 0)

        accept_button = gui.Button(("OK"))
        menu_table.add(accept_button, 0, 1)
        accept_button.connect(gui.CLICK, self.recover, None)

        self.app.run(menu_table)

#****************************************************************************
#  Return to main menu.
#****************************************************************************
    def recover(self, obj):
        self.app.quit()
        MainMenu(self.client)

#****************************************************************************
#
#****************************************************************************
class MenuBackground(gui.Widget):
    def __init__(self,**params):
        gui.Widget.__init__(self,**params)
        client = params['client']
        filename = os.path.join('data', 'graphics', 'misc', 'menubackground.jpg')
        surface = tileset.load(filename)
        scale = float(client.screen.get_width()) / surface.get_width()
        self.surface = pygame.transform.rotozoom(surface, 0, scale)

#****************************************************************************
#
#****************************************************************************
    def paint(self,s):
        s.blit(self.surface,(0,0))

#****************************************************************************
#
#****************************************************************************
class CreditScreen():
    def __init__(self):
        placeholder = True

    def credits(self):
        placeholder = True
