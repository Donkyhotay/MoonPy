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

import os
import pygame
import logging
import tileset
from time import sleep

#****************************************************************************
#  The Introscreen shows a splash image. FIXME: Video, sound etc...
#****************************************************************************

class IntroScreen:
    def __init__(self, screen):
        image = "data/graphics/misc/intro_splash.png"
        screen = pygame.display.set_mode((550,550))
        try:
            splashScreen = pygame.image.load(image)
        except pygame.error, message:
            print 'Cannot load splash image'
            raise SystemExit, message
        splashScreen = splashScreen.convert()
        screen.blit(splashScreen, (0,0))
        pygame.display.flip()
        sleep(2)
        screen = pygame.display.set_mode((1024,768))



