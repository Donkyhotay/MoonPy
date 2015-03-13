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
class ConnInfo:
    def __init__(self, client_ref, name, address, playerID, energy, Idisabled, reload, Ireloading):
        self.ref = client_ref
        self.name = name
        self.username = []
        self.username.append(0)
        self.address = address
        self.playerID = []
        self.playerID.append(0)
        self.teamID = []
        self.teamID.append(0)
        self.energy = []
        self.energy.append(0)
        self.undisable = []
        self.undisable.append(False)
        self.Idisabled = [0]
        self.reload = []
        self.reload.append(False)
        self.Ireloading = [0]
