#
# eurotherm2200.py (c) Stuart B. Wilkins 2008
#
# $Id: eurotherm.py 85 2009-01-04 20:48:14Z swilkins $
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/iomodules/eurotherm.py $
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

import logging as log
logging = log.getLogger(__name__)

class Eurotherm2000(objects.VacObject):
    CID    = 0 # CONTROLLERID
    PV     = 1 # PROCESS VARIABLE
    STAT   = 2 # STATUS
    SP     = 3 # SETPOINT
    SP1    = 4 # SP1
    SP2    = 5 # SP2
    SSEL   = 6 # Setopint Select
    UNITS  = 7

    ModbusAddress = {
        #                  ( Address, Bytes to read, conv factor )
        CID              : ( 122, 1, 1),
        PV               : ( 1, 1, 10),
        SP               : ( 2, 1, 10),
        STAT             : ( 23, 1, 1),
        SP1              : ( 24, 1, 10),
        SP2              : ( 25, 1, 10),
        SSEL             : ( 15, 1, 1),
        UNITS            : ( 516, 1, 1)
    }

    def __init__(self, host, unit = 1):
        objects.VacObject.__init__(self)
        self.unit = unit
        self.host = host
        
        logging.debug("Eurotherm2000.__init___ : port = %s, unit = %d" %
                      (self.host, self.unit))

        self.com = modbus.ModbusTCPIP(host, unit = unit,
                                      mode = modbus.ModbusTCPIP.SERIAL)
        
        self.values = {}
        self.status = 0
        
    def update(self):
        self.status = self.ERROR
        for mba in self.ModbusAddress:
            f, s = self.com.request(3, # Code to read address 
                                    self.ModbusAddress[mba][0], 
                                    self.ModbusAddress[mba][1])
            if f:
                if self.ModbusAddress[mba][2] is not 1:
                    self.values[mba] = float(s) / self.ModbusAddress[mba][2]
                else:
                    self.values[mba] = s
                self.status = self.ON
        return True

    def getUnits(self, chan):
        return "degC"

    def getValue(self, chan):
        return self.values[self.PV]

    def getStatus(self, chan):
        return self.status

if __name__ == "__main__":
    log.basicConfig()
    e = Eurotherm2000(("localhost", 4001), unit = 2)
    e.update()
