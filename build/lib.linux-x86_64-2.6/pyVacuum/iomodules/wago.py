#
# wago.py (c) Stuart B. Wilkins 2008
#
# $Id: wago.py 106 2009-10-12 00:16:17Z swilkins $
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/iomodules/wago.py $
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

from modbus import *
from objects import *

import logging as log
logging = log.getLogger(__name__)

class WagoValve(VacObject):
    def __init__(self, host, opaddr = [0], ipaddr = [0], mode = None):
        VacObject.__init__(self)
        self.com = ModbusTCPIP(host = host)
        
        self.opaddr = opaddr
        self.ipaddr = ipaddr

        if mode == None:
            self.mode = [0 for i in self.opaddr]
        else:
            self.mode = mode

        self.status = [self.ERROR for i in self.opaddr]
        for n in self.opaddr:
            self.status.append(self.ERROR)
        self.initialized = False

    def init(self):
        self.initialized = True
        return True

    def getActions(self, chan):
        if self.mode != 2:
            dict = { "OPEN" : self.OPEN,
                     "CLOSE" : self.CLOSE }
        else:
            dict = {}
            
        return dict

    def update(self):
        for n in range(len(self.opaddr)):
            # Read both the status of the coil and switches
            f, sw = self.com.request(1, self.ipaddr[n], 2)
            if(self.mode[n] != 2):
                f, op = self.com.request(1, 0x0200 + self.opaddr[n], 1)
                
            if self.mode[n] == 0:
                if ((op == 1) & (sw == 1)):
                    self.status[n] = self.OPEN
                elif ((op == 0) & (sw == 2)):
                    self.status[n] = self.CLOSE
                else:
                    self.status[n] = self.ERROR
            else:
                if sw == 1:
                    self.status[n] = self.OPEN
                elif sw == 2:
                    self.status[n] = self.CLOSE
                else:
                    self.status[n] = self.ERROR
                
                    
    def getStatus(self, unit):
        # Get two bits for valve status
        return self.status[unit]

    def setStatus(self, unit, status):
        if self.mode[unit] == 0:
            if status == self.OPEN:
                s = self.com.request(5, self.opaddr[unit], 0xFF00)
            elif status == self.CLOSE:
                s = self.com.request(5, self.opaddr[unit], 0x0000)
            else:
                return False
            if s[0] != True:
                return False
        elif self.mode[unit] == 1: 
            if status == self.OPEN:
                c = 0
                s = self.com.request(5, self.opaddr[unit] + 1, 0x0000)
            elif status == self.CLOSE:
                c = 1
                s = self.com.request(5, self.opaddr[unit], 0x0000)
            else:
                return False
                
            s = self.com.request(5, self.opaddr[unit] + c, 0xFF00)
            t = time.time()
            flag = False
            while((time.time() - t) < 15):
                s, f = self.com.request(1, self.ipaddr[unit] + c, 1)
                time.sleep(0.1)
                if f:
                    break
            
            s = self.com.request(5, self.opaddr[unit] + c, 0x0000)
        else:
            return False

        return True

    def getValue(self, unit):
        if self.status[unit] == self.OPEN:
            return 1
        else:
            return 0

class WagoBackPump(VacObject):
    def __init__(self, host, opaddr = [0]):
        VacObject.__init__(self)
        self.com = ModbusTCPIP(host = host)
        self.opaddr = opaddr
        self.status = []
        self.value = []
        for n in self.opaddr:
             self.value.append(0.0)
             self.status.append(self.ERROR)

    def update(self):
        x = 0
        for addr in self.opaddr:
            a, b = self.com.request(1, addr + 0x200, 1)
            if a == True:
                if b == True:
                    self.status[x] = self.ON
                    self.value[x] = b
                else:
                    self.status[x] = self.OFF
                    self.value[x] = 0.0
                x = x + 1
            else:
                self.status[x] = self.ERROR
                self.value[x] = 0.0

    def getActions(self, chan):
        dict = { "ON" : self.ON  ,
                 "OFF" : self.OFF }
        return dict

    def getValue(self, chan):
        return self.value[chan]
    
    def getStatus(self, chan):
        return self.status[chan]
    
    def setStatus(self, chan, status):
        if status == self.ON:
            s = self.com.request(5, self.opaddr[chan], 0xFF00)
        if status == self.OFF:
            s = self.com.request(5, self.opaddr[chan], 0x0000)
        else:
            return False
        
        if s[0] != True:
            logging.warning("setStatus() : Failed to set status")
            return False

        return True

class WagoDigit(VacObject):
    def __init__(self, host, ipaddr = [], mode = None):
        VacObject.__init__(self)
        self.com = ModbusTCPIP(host = host)
        
        self.ipaddr = ipaddr
        if mode is None:
            self.mode = []
            for n in self.ipaddr:
                self.mode.append('')
        else:
            self.mode = mode
        
        self.status = []
        for n in self.ipaddr:
            self.status.append(0.0)


    def update(self):
        x = 0
        for addr in self.ipaddr:
            allval = []
            for iaddr in addr:
                a, b = self.com.request(1, iaddr, 1)
                if a == False:
                    self.status[x] = self.ERROR
                    break
                allval.append(b)
            
            val = allval[0]
            for n in allval[1:]:
                if self.mode[x] == 'or':
                    val = val or n
                elif self.mode[x] == 'and':
                    val = val and n
                    
            if val:
                self.status[x] = self.ON
            else:
                self.status[x] = self.OFF
            
            x = x + 1
            
    def getStatus(self, chan):
        return self.status[chan]
    def getValue(self, chan):
        return self.status[chan]

class WagoSensor(VacObject):
    RAW = 0
    TYPEK469 = 1 
    def __init__(self, host, ipaddr = [], type = RAW):
        VacObject.__init__(self)
        self.com = ModbusTCPIP(host = host)
        self.type = type
        self.ipaddr = ipaddr
        self.status = []
        self.value = []
        for n in self.ipaddr:
            self.value.append(0.0)
            self.status.append(0.0)

    def getActions(self, chan):
        return{}

    def getUnits(self, chan):
        if self.type == self.TYPEK469:
            return "degC"
        else:
            return "mV"

    def update(self):
        x = 0
        for addr in self.ipaddr:
            a, b = self.com.request(4, addr, 1)
            if a == True:
                self.status[x] = self.ON
                self.value[x] = b
            else:
                self.status[x] = self.ERROR
                self.value[x] = 0.0

            x = x + 1

    def getValue(self, chan):
        if self.type == self.TYPEK469:
            return self.value[chan] / 10.0
        else:
            return self.value[chan] 
    
    def getStatus(self, chan):
        return self.status[chan]

class NT10Turbo(VacObject):
    RESET = 0x100
    def __init__(self, host, opaddr = [0], ipaddr = [0]):
        VacObject.__init__(self)
        self.com = ModbusTCPIP(host = host)
        self.opaddr = opaddr
        self.ipaddr = ipaddr

        self.status = []
        self.statusMessage = []
        for i in self.opaddr:
            self.statusMessage.append("")
            self.status.append(0)

    def getActions(self, chan):
        dict = { "ON" : self.ON ,
                 "OFF" : self.OFF }

        return dict

    def hasValue(self, unit):
        return False

    def update(self):
        x = 0
        for i in self.ipaddr:
            r, s = self.com.request(1, i, 2)
            logging.debug("getStatus() : Conroller responded %d" % s)
            if r != True:
                self.status[x] = self.ERROR
            else:
                self.status[x] = s

    def getStatus(self, unit):
        s = self.status[unit]
        
        # Acceleration Signal
        #if s & 0x2:
        #    self.statusMessage[unit] = "ACCELERATING"
        #    return self.ACCEL

        # Normal Signal
        if s == 0x02:
            self.statusMessage[unit] = ""
            return self.OFF

        # ON Signal
        if s == 0x03:
            self.statusMessage[unit] = ""
            return self.ON

        return self.ERROR

    def getStatusMessage(self, unit):
        return self.statusMessage[unit]

    def getValue(self, unit):
        return self.status[unit]

    def setStatus(self, a, s):
        if s == self.ON:
            r = self.com.request(5, self.opaddr[a], 0xFF)
        elif s == self.OFF:
            r = self.com.request(5, self.opaddr[a], 0x00)
       

class STP451Turbo(VacObject):
    RESET = 0x100
    def __init__(self, host, opaddr = [0], ipaddr = [0]):
        VacObject.__init__(self)
        self.com = ModbusTCPIP(host = host)
        self.opaddr = opaddr
        self.ipaddr = ipaddr

        self.status = []
        self.statusMessage = []
        for i in self.opaddr:
            self.statusMessage.append("")
            self.status.append(0)

    def getActions(self, chan):
        dict = { "ON" : self.ON ,
                 "OFF" : self.OFF , 
                 "RESET" : self.RESET }

        return dict

    def hasValue(self, unit):
        return False

    def update(self):
        x = 0
        for i in self.ipaddr:
            r, s = self.com.request(1, i, 5)
            logging.debug("getStatus() : Conroller responded %d" % s)
            if r != True:
                self.status[x] = self.ERROR
            else:
                self.status[x] = s

    def getStatus(self, unit):
        s = self.status[unit]

        # Remote Mode
        if not (s & 0x16):
            self.statusMessage[unit] = "LOCAL MODE"
            return self.ERROR

        # Fault Indicator
        if not (s & 0x2):
            self.statusMessage[unit] = "FAULT"
            return self.FAULT
        
        # Acceleration Signal
        if s & 0x4:
            self.statusMessage[unit] = "ACCELERATING"
            return self.ACCEL
        # Brake Signal
        if s & 0x8:
            self.statusMessage[unit] = "BRAKE"
            return self.BRAKE

        # Normal Signal
        if s == 0x13:
            self.statusMessage[unit] = ""
            return self.OFF

        # Error Signal
        if s == 0x12:
            self.statusMessage[unit] = ""
            return self.ON

        return self.ERROR

    def getStatusMessage(self, unit):
        return self.statusMessage[unit]

    def getValue(self, unit):
        return self.status[unit]

    def setStatus(self, a, s):
        if s == self.ON:
            r = self.com.request(5, self.opaddr[a] + 1, 0xFF00)
        elif s == self.OFF:
            r = self.com.request(5, self.opaddr[a] + 1, 0x0000)
        elif s == self.RESET:
            r = self.com.request(5, self.opaddr[a], 0xFF00)
            time.sleep(5)
            r = self.com.request(5, self.opaddr[a], 0x0000)
        
