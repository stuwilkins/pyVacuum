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

from pyVacuum.log import setupLog
logging = setupLog(__name__)

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

    NotSettable = 0
    ValueSettable = 2
    StatusSettable = 3
    

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
        self.needsPolling = True
        self.callbacks = []
        return

    def init(self):
        self.initialized = True
        return True
    
    def close(self):
        return True

    def isInitialized(self, chan):
        return self.initialized

    def getActions(self, chan):
        return {}

    def getUnits(self, chan):
        return "None"

    def getStatusMessage(self, chan):
        return "" 

    def needsPoll(self):
        return self.needsPolling

    def addCallback(self, callback):
        if callback in self.callbacks:
            logging.debug("addCallback() : Callback %s exists", str(callback))
            return False
        else:
            self.callbacks.append(callback)
            return True

    def removeCallback(self,callback):
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            logging.debug("removeCallback() : Removed %s", str(callback))

    def emitCallback(self, *args, **kwargs):
        for cb in self.callbacks:
            cb(self, *args,**kwargs)

    def getInformation(self, chan):
        return "Sorry, no information for this device.",""

    def isSettable(self, chan):
        return self.NotSettable

    def setStatus(self, chan):
        return False

    def setValue(self, chan):
        return False

    


