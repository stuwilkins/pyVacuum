#
# x1und.py (c) Stuart B. Wilkins 2008
#
# $Id: nsls.py 110 2009-10-19 01:51:28Z swilkins $
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

import sys
import socket
from objects import *

class NSLSRingStatus(VacObject):
    def __init__(self, host = None):
        VacObject.__init__(self)
        self.value = 0
        self.status = self.OFF
        self.host = host
        self.sock = None
        self.cmdstring = ""

    def update(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(self.host)
        except:
            logging.warn("update() : Connect to %s failed." % self.host[0])
            return False

        self.sock.send("G?")
        
        try:
            r = self.sock.recv(1024)
        except:
            logging.warning("update() : Failed to receive reply")
            self.sock.close()
            return False
    
        self.sock.close()
        self.cmdstring = r
        try:
            self.value = float(self.cmdstring.split(",")[1])
        except:
            logging.warning("update() : Unable to convert float value")
            return False

        self.emitCallback()
        return True

    def getUnits(self, unit):
        return "mm"

    def getStatus(self, unit):
        return self.status

    def getValue(self, unit):
        return self.value

if __name__ == "__main__":
    a = NSLSRingStatus(host = ("172.16.1.129", 4002))
    a.update()
    print a.getValue(0)
