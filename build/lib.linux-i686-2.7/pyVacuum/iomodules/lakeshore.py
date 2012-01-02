#
# lakeshore.py (c) Stuart B. Wilkins 2008
#
# $Id: lakeshore.py 109 2009-10-19 00:12:25Z swilkins $
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

import modbus
import objects
import socket
socket.setdefaulttimeout(10)

import logging as log
logging = log.getLogger(__name__)

class Lakeshore(objects.VacObject):
    def __init__(self, host, nsensors = 2):
        objects.VacObject.__init__(self)
        
        self.host = host
        
        logging.debug("Lakeshore.__init___ : host = %s:%s" %
                      (self.host))

        self.temperatures = []
        self.tempstatus = []
        for i in range(nsensors + 1):
            self.temperatures.append(0.0)
            self.tempstatus.append(0)
        self.others = [0.0, 0.0]
        self.nsensors = nsensors
        
    def getActions(self, chan):
        return {}
    
    def update(self):
        """Update controller by reading all parameters from lakeshore"""
        if self.connect() != True:
            return False

        self.readTemperatures()
        
        self.close()
        return True

    def getValue(self, unit):
        if unit >= 10:
            return self.others[unit - 10]
        else:
            return self.temperatures[unit]

    def getStatus(self, unit):
        if unit >= 10:
            return self.ON
        
        if self.tempstatus[unit] == 0:
            return self.ON
        else:
            return self.FAULT
    
    def getStatusMessage(self, unit):
        if unit >= 10:
            return ""
        if self.tempstatus[unit] == 0:
            return ""
        if self.tempstatus[unit] & 16:
            return "Ur"
        if self.tempstatus[unit] & 32:
            return "Or"
        if self.tempstatus[unit] & 64:
            return "0"
        if self.tempstatus[unit] & 128:
            return "Or"

    def readTemperatures(self):
        """Read Temperatures from Lakeshore"""
        c, val = self.readCommand("SETP?")
        if c == True:
            try:
                self.temperatures[0] = float(val)
            except:
                self.temperatures[0] = 0.0
        c, val = self.readCommand("HTRST?")
        if c == True:
            try:
                self.tempstatus[0] = int(val)
            except:
                self.tempstatus[0] = 0
                
        for i in range(self.nsensors):
            c, val = self.readCommand("KRDG? %c" % (chr(65 + i)))
            if c == True:
                try:
                    self.temperatures[i + 1] = float(val)
                except:
                    self.temperatures[i + 1] = 0.0
                    
            c, val = self.readCommand("RDGST? %c" % (chr(65 + i)))
            
            if c == True:
                try:
                    self.tempstatus[i + 1] = int(val)
                except:
                    self.tempstatus[i + 1] = 0

        cmds = ["RANGE?", "HTR?"]
        for i in range(len(cmds)):
            c, val = self.readCommand(cmds[i])
            if c == True:
                try:
                    self.others[i] = float(val)
                except:
                    self.others[i] = 0.0
            
        return True

    def connect(self):
        """Open the socket for communications"""
        self.commport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.commport.connect(self.host)
        except:
            logging.critical("Failed connect to %s" % self.host[0])
            return False
        
        return True

    def close(self):
        """Close the commport"""
        self.commport.close()

    def readCommand(self, cmd):
        """Send a command to the lakeshore and receive a reply"""
        logging.debug("sendcommand() : %s" % cmd)
        try:
            self.commport.sendall("%s%c" % (cmd, 13))
        except:
            logging.critical("readCommand() : Unable to send data")
            return False, ""
         
        try:
            s = self.commport.recv(1024)
        except:
            logging.critical("readCommand() : error reading from socket.")
            return False, ""
         
        s = s[:-1]
        logging.debug("readCommand() : %s" % s)
        return True, s
     
    def sendCommand(self, cmd):
        """Send a command to the lakeshore (no reply)"""
        logging.debug("sendcommand() : %s" % cmd)
        try:
            self.commport.sendall("%s%c" % (cmd, 13))
        except:
            logging.critical("readCommand() : Unable to send data")
            return False
        try:
            s = self.commport.recv(1024)
        except:
            logging.critical("readCommand() : error reading from socket.")
            return False
         
        return True

if __name__ == "__main__":
    test  = Lakeshore(host = ('localhost', 3004))
    test.update()
