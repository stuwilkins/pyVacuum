#
# gammampc.py (c) Stuart B. Wilkins 2008
#
# $Id: gammampc.py 98 2009-07-20 21:28:57Z swilkins $
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

import socket
socket.setdefaulttimeout(10)

from objects import *

import logging as log
logging = log.getLogger(__name__)
#logging.setLevel(log.DEBUG)
#ch = log.StreamHandler()
#ch.setLevel(log.DEBUG)
#logging.addHandler(ch)

class GammaMPC(VacObject):
    GaugeStart = 16
    MaxChan = 2
    def __init__(self, host, unit = 0):
        VacObject.__init__(self)
        self.inetaddr = host
        self.unit = unit

        logging.debug("GammaMPC init : Host = %s, unit = %d" %
                      (self.inetaddr[0], self.unit))

        # So far we have 2 This should be placed in init

        self.pressures = []
        self.pressuresUnits = []
        self.currents = []
        self.currentsUnits = []
        self.status = []
        self.statusMessage = []
        for i in range(self.MaxChan):
            self.pressures.append(0.0)
            self.currents.append(0.0)
            self.pressuresUnits.append("None")
            self.currentsUnits.append("None")
            self.status.append(self.ERROR)
            self.statusMessage.append("")

    def init(self):
        """
        This controller does not INIT but we will ask for the
        ident string to check communications.

        Returns True if OK, False if error.
        """
        self.initialized = False
        if self.connect() == True:
            b, s = self.readString("01", 1)
            self.close()
            if not b:
                return False
            self.initialized = True
            return True
        
        return False

    def getActions(self, chan):
        if self.unit < self.GaugeStart:
            dict = { "ON" : self.ON ,
                     "OFF" : self.OFF }
        else:
            dict = {}
        
        return dict

    def hasValue(self, unit):
        return True
    
    def getValue(self, unit):
        if unit < self.GaugeStart:
            return self.currents[unit]
        else:
            return self.pressures[unit - self.GaugeStart]

    def getUnits(self, unit):
        if unit < self.GaugeStart:
            return self.currentsUnits[unit]
        else:
            return self.pressuresUnits[unit - self.GaugeStart]
        
    def getStatus(self, unit):
        if unit < self.GaugeStart:
            return self.status[unit]
        else:
            return self.status[unit - self.GaugeStart]

    def getStatusMessage(self, unit):
        if unit < self.GaugeStart:
            return self.statusMessage[unit]
        else:
            return ""
        
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(self.inetaddr)
        except:
            logging.debug("Connect to %s failed" % self.inetaddr[0])
            return False

        return True

    def close(self):
        self.sock.close()

    def update(self):
        if not self.tryUpdate():
            for i in range(self.MaxChan):
                self.pressures[i] = -1.0
                self.currents[i] = -1.0
                self.pressuresUnits[i] = "None"
                self.currentsUnits[i] = "None"
                self.status[i] = self.ERROR
                self.statusMessage[i] = ""
            return False
        return True

    def tryUpdate(self):
        if not self.connect():
            return False
        if not self.readPressures():
            return False
        if not self.readCurrents():
            return False
        if not self.readStatus():
            return False
        self.close()
        return True
        
    def sendCommand(self, c, d = []):
        # Start with the ~

        s = "~ %02d %s " % (self.unit, c)
        
        for i in range(len(d)):
            s = s + d[i] + " "

        # Calculate checksum

        csum = 0
        for i in range(1, len(s)):
            csum = csum + ord(s[i])

        s = s + "%02x" % (csum & 0xFF)
        logging.debug("sendCommand() : %s" % s)

        try:
            self.sock.sendall("%s\n" % s)
        except:
            logging.critical("sendCommand() : sendall failed")
            return False

        return True

    def readCommand(self):

        try:
            s = self.sock.recv(1024)
        except:
            logging.critical("readCommand() : sock.recv() failed")
            return False, [""]
        
        s = s[:-1] # Remove \n
        logging.debug("readcommand() : %s" % s)

        # Remove checksum
        csum = s[-2:]
        s = s[:-3]

        if s[0:2] != ("%02d" % self.unit):
            return False, [""]

        if s[3:5] != "OK":
            return False, [""]

        s = s[6:].split(" ")
            
        return True, s

    def readValue(self, code, n):

        if not self.sendCommand(code, [ "%d" % n ]):
            return False, -1.0

        f, r = self.readCommand()
        if not f:
            return False, -1.0
        try:
            v = float(r[1])
            if len(r) > 2:
                return True, v, r[2]
            else:
                return True, v, ""
        except:
            return False, -1.0
        
    def readString(self, code, n):
        if not self.sendCommand(code, [ "%d" % n ]):
            return False, ""

        b, r = self.readCommand()
        if not b:
            return False, ""

        return True, r[1:]

    def sendValue(self, code, n):
        if not self.sendCommand(code, [ "%d" % n ]):
            return False

        a, b = self.readCommand()
        return a
        
    def readPressures(self):
        for n in range(2):
            b, x, y = self.readValue("0B", n + 1)
            if not b:
                return False
            self.pressures[n] = x
            self.pressuresUnits[n] = y
        return True

    def readCurrents(self):
        for n in range(2):
            b, x, y = self.readValue("0A", n + 1)
            if not b:
                return False
            self.currents[n] = x
            self.currentsUnits[n]= y
        return True

    def readStatus(self):
        flag = True
        for n in range(2):
            b, r = self.readString("0D", n + 1)
            if not b:
                self.status[n] = self.ERROR
                flag = False
            elif r[0] == "RUNNING":
                self.status[n] = self.ON
            elif r[0] == "STANDBY":
                self.status[n] = self.OFF
            else:
                self.status[n] = self.FAULT
                
            self.statusMessage[n] = r[0]
       
        return flag

    def setStatus(self, chan, onoff):
        self.connect()
        if onoff == self.ON:
            return self.sendValue("37", chan + 1)
        elif onoff == self.OFF:
            return self.sendValue("38", chan + 1)

        return False

if __name__ == "__main__":
    p = GammaMPC(("localhost", 3002),0)
    p.init()
    p.connect()
    print p.readString('73', 1)
    p.close()
#
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/iomodules/gammampc.py $
#

