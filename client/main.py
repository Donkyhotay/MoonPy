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
import pygame
import gettext
import platform
import sys
import os
import time

import introscreen  

from networkclient import *
from gameclientstate import *
from mainmenu import *


#****************************************************************************
# The Main class of the client. 
#****************************************************************************
class Main:

    def __init__(self, debug, skipintro):
        pygame.init()

        tetherdir = os.getenv("HOME")
        if str(tetherdir) == "None":
            tetherdir = os.getenv("USERPROFILE")
            tetherdir = os.path.join(tetherdir, "moonpy")
        else:
            tetherdir = os.path.join(tetherdir, ".moonpy")
        if not os.path.exists(tetherdir):
            os.mkdir(tetherdir)
        logfile = os.path.join(tetherdir, "MoonPy.log")
        if os.path.exists(logfile):
            os.remove(logfile)
        if debug == True:
            logLevel = logging.INFO
            logging.basicConfig(level=logging.DEBUG)
        else:
            LOG_FILENAME = logfile
            logging.basicConfig(filename=LOG_FILENAME,level=logging.INFO)

        logging.info('Platform: ' + platform.platform())
        logging.info('Python version ' + sys.version)
        logging.info('Pygame version: ' + pygame.version.ver)

        self.client = GameClientState()
        self.client.debug = debug
        logging.info("MoonPy version %s" % (self.client.settings.string_version))

        if skipintro == True:
            time.sleep(1)
            self.create_main_window()
            self.client.moonaudio.intro()
        else:
            self.create_main_window()
            self.client.moonaudio.intro()
            self.intro = introscreen.IntroScreen(self.client.screen)

        mainmenu = MainMenu(self.client)


#****************************************************************************
#
#****************************************************************************
    def create_main_window(self):
        screen_width = self.client.settings.screen_width 
        screen_height = self.client.settings.screen_height 
        screen_mode = 0
        screen = pygame.display.set_mode((500, 500), screen_mode)

        pygame.display.set_caption("Welcome to MoonPy")
        self.client.screen = screen

