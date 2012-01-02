#
# objects.py (c) Stuart B. Wilkins 2008
#
# $Id: objects.py 107 2009-10-12 20:00:40Z swilkins $
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/iomodules/objects.py $
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import time

import logging as log
logging = log.getLogger(__name__)

class VacObject:
    """
    A general class for vacuum objects
    """

    ERROR = 0
    ON = 1
    OFF = 2
    ACCEL = 3
    BRAKE = 4
    FAULT = 5
    DEGAS = 6
    SETATM = 7
    SETVAC = 8
    SWAPFILL = 9
    OPEN = 11
    CLOSE = 12

    NICETEXT = {
        ERROR : 'ERROR', 
        ON : 'ON',
        OFF : 'OFF',
        ACCEL : 'ACCEL',
        BRAKE : 'BRAKE',
        FAULT : 'FAULT', 
        DEGAS : 'DEGAS',
        SETATM : 'SETATM',
        SETVAC : 'SETVAC',
        SWAPFILL : 'SWAPFILL',
        OPEN : 'OPEN',
        CLOSE : 'CLOSE'}

    def __init__(self):
        self.initialized = False
        return

    def init(self):
        self.initialized = True
        return True

    def isInitialized(self, chan):
        return self.initialized

    def getActions(self, chan):
        return {}

    def getUnits(self, chan):
        return "None"

    def getStatusMessage(self, chan):
        return "" 

    


