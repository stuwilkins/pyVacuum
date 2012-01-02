#
# varianmg.py (c) Stuart B. Wilkins 2008
#
# $Id: varianmg.py 76 2009-01-03 05:17:52Z swilkins $
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/iomodules/varianmg.py $
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

import logging as log
try:
    import serial
except:
    pass

import socket
socket.setdefaulttimeout(10)

logging = log.getLogger(__name__)
from objects import *

class VarianMGVac(VacObject):

    SERIAL = 0
    SOCKET = 1
    NMAX = 10

    def __init__(self, port, mode = None, unit = 0):
        VacObject.__init__(self)
        self.unit = unit
        self.port = port

        self.pressures = []
        self.status = []
        self.params = []
        self.statusMessage = []
        for n in range(self.NMAX):
            self.pressures.append(-1.0)
            self.status.append(self.ERROR)
            self.statusMessage.append("")

        self.units = "None"

        if mode == None: 
            self.mode = self.SERIAL
        else:
            self.mode = mode

        logging.debug("VarianMGVac.__init___ : port = %s:%d, mode = %d" %
                      (self.port[0], self.port[1], self.mode))

        self.initialized = False

    def init(self):
        if self.connect() == False:
            return False
        if self.initController() == False:
            return False
        self.close()
        
        logging.debug("init() sucsesfull")
        self.initialized = True
        
        return True

    def getActions(self, chan):
        type = self.params[chan][0]
        if (type == "UHV") or (type == "BA"):
            dict = { "ON" : self.ON ,
                     "OFF" : self.OFF, 
                     "DEGAS" : self.DEGAS,
                     "SWAP FILL" : self.SWAPFILL}
        elif (type == "CC") or (type == "IM"):
            dict = { "ON" : self.ON ,
                     "OFF" : self.OFF}
        elif (type == "CT") or (type == "TC"):
            dict = { "Set ATM" : self.SETATM,
                     "Set VAC" : self.SETVAC}
        else:
            return {}
        return dict

    def getValue(self, chan):
        return self.pressures[chan]
    
    def getUnits(self, chan):
        return self.units
    
    def getStatus(self, chan):
        if self.pressures[chan] < 0:
            return self.ERROR
        return self.status[chan]

    def getStatusMessage(self, chan):
        return self.statusMessage[chan]
        
    def update(self):
        if not self.tryUpdate():
            for n in range(self.NMAX):
                self.pressures[n] = -1.0
                self.status[n] = self.ERROR
                self.statusMessage[n] = ""

            return False
        else:
            return True

    def tryUpdate(self):
        if not self.connect():
            return False

        if not self.readPressures():
            self.close()
            return False

        if not self.readStatus():
            self.close()
            return False
        
        self.close()
        return True
        
    def close(self):
        self.commport.close()

    def connect(self):
        """
        Open the serial port for communications
        """
        if self.mode == self.SERIAL:
            try:
                self.commport = serial.Serial(self.port, 9600,
                                              bytesize = 8, parity = 'N',
                                              stopbits = 1, timeout = 5)
            except:
                logging.critical("Failed connect to %s" % self.port[0])
                return False

        elif self.mode == self.SOCKET:
            self.commport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.commport.connect(self.port)
            except:
                logging.critical("Failed connect to %s" % self.port[0])
                return False

        return True


    def initController(self):
        if not self.connect():
            return False
          
        x, r = self.send("01")
        if not x:
            return False

        # Read all slots and assign 

        if len(r) != 10:
            logging.critical("initController() : malformed string")
            return False
        
        self.boards = []
        self.pboards = []
        self.tboards = []
        self.npressures = []
        for i in range(10):
            t = r[i:i+2]
            if t == "10":
                self.boards.append("UHV")
                self.npressures.append(1)
                self.pboards.append("UHV")
                self.tboards.append("I")
            elif t == "20":
                self.boards.append("BA")
                self.npressures.append(1)
                self.pboards.append("BA")
                self.tboards.append("I")
            elif t == "30":
                self.boards.append("BA")
                self.npressures.append(1)
                self.pboards.append("BA")
                self.tboards.append("I")
            elif t == "38":
                self.boards.append("CC")
                self.npressures.append(1)
                self.pboards.append("CC")
                self.tboards.append("I")
            elif t == "3A":
                self.boards.append("IM")
                self.npressures.append(1)
                self.pboards.append("IM")
                self.tboards.append("I")
            elif t == "40":
                self.boards.append("TC")
                self.npressures.append(4)
                self.pboards.append("TC")
                self.tboards.append("T")
            elif t == "42":
                self.boards.append("GP")
                self.npressures.append(4)
                self.pboards.append("GP")
                self.tboards.append("T")
            elif t == "4C":
                self.boards.append("CDG")
                self.npressures.append(2)
                self.pboards.append("CDG")
                self.tboards.append("A")
            elif t == "48":
                self.boards.append("CT")
                self.npressures.append(2)
                self.pboards.append("CT")
                self.tboards.append("T")
            elif t == "50":
                self.boards.append("SP")
            elif t == "60":
                self.boards.append("RM")
            else:
                self.boards.append("NONE")

        icount = 0
        tcount = 0
        acount = 0
        self.params = []
        for i in range(len(self.npressures)):
            for j in range(self.npressures[i]):
                if self.tboards[i] == "I":
                    count = icount
                    icount = icount + 1
                elif self.tboards[i] == "T":
                    count = tcount
                    tcount = tcount + 1
                elif self.tboards[i] == "A":
                    count = acount
                    acount = acount + 1
                else:
                    print tboards[i]
                    
                self.params.append((self.pboards[i],
                                    self.tboards[i],
                                    count))
 
        self.close()
        return True

    def readPressures(self):
        x, y = self.send("13")
        if not x:
            logging.critical("readPressures() : error reading units")
            return False

        if y == "00":
            self.units = "Torr"
        elif y == "01":
            self.units = "mBar"
        elif y == "02":
            self.units = "Pascal"
        else:
            self.units = "Unknown"
        
        x, y = self.send("0F")
        if not x:
            logging.critical("readPressures() : error reading pressure dump")
            return False
        
        y = y.split(","); i = 0; j = 0
        for n in range(len(self.npressures)):
            for m in range(self.npressures[n]):
                if i >= len(y):
                    logging.critical("readPressures() : number of gauges mismach")
                    return False

                if y[i][0] != "E":
                    try:
                        self.pressures[j] = float(y[i])
                    except:
                        logging.critical("readPressures() : Error converting pressure to float")
                        self.pressures[j] = -1.0
                else:
                    self.pressures[j] = -1.0
                    
                i = i + 1
                j = j + 1
                # Skip over problem with convec-torr
            
            if self.pboards[n] == "CT":
                i = i + 2
                
        return True

    def readStatus(self):
        
        logging.debug("readStatus() : START")
        for n in range(len(self.params)):
            logging.debug("readStatus() : Gauge %d" % n)
            if self.params[n][1] == "I":
                # UHV, BA, CC, IM                
                logging.debug("readStatus() : Gauge I %d" % n)
                x, y = self.readDegas(n)
                if not x:
                    logging.critical("readStatus() : Error reading params")
                    return False

                if y == 1:
                    self.status[n] = self.DEGAS
                else:
                    x, y = self.readEmission(n)
                    if not x:
                        logging.critical("readStatus() : Error reading params")
                        return False
                    if y == 0:
                        self.status[n] = self.OFF;
                    elif y == 1:
                        self.status[n] = self.ON;
                    else:
                        self.status[n] = self.ERROR
                
                # Read lit filiament

                type = self.params[n][0]
                if (type == "UHV") or (type == "BA"):
                    if self.status[n] == self.ON:
                        x, y = self.getFiliamentLit(n)
                        if not x:
                            logging.critical("readStatus() : error getting lit filiament")
                            return False
                        if y:
                            self.statusMessage[n] = "Filament %d" % x
                        else:
                            self.statusMessage[n] = ""
                else:
                    self.statusMessage[n] = ""

            else:
                self.status[n] = self.ON
                self.statusMessage[n] = ""

        logging.debug("readStatus() : END")
        return True
                
    def setStatus(self, chan, status):
        if not self.connect():
            logging.critical("setStatus() : could not connect")
            return False
        logging.debug("setStatus() : %d" % status)
        if status == self.ON:
            x = self.setEmission(chan, True)
        elif status == self.OFF:
            x = self.setEmission(chan, False)
        elif status == self.DEGAS:
            x = self.setDegas(chan, True)
        elif status == self.SWAPFILL:
            x = self.setFil2(chan)
        elif status == self.SETATM:
            x = self.setAtm(chan)
        self.close()
            
        return x

    def readEmission(self, chan):
        board = self.params[chan][2] + 1
        x, y = self.send("32I%1d" % board)
        if not x:
            return False, 0

        if y == "00":
            return True, False
        elif y == "01":
            return True, True
        
        logging.critical("readEmission() : malformed responce")
        return False, False
        
    def setEmission(self, chan, on = True):
        """
        Set the emission (turn the gauge on!)
        Check board type to be able to do this

        """

        board = self.params[chan][2]

        if on:
            s = "31I%1d" % (board + 1)
        else:
            s = "30I%1d" % (board + 1)

        x, y = self.send(s)
        return x

    def setAtm(self, chan):
        board = self.params[chan][2] + 1
        x, y = self.send("A1T%1d" % board)
        return x

    def setVac(self, chan):
        board = self.params[chan][2] + 1
        x, y = self.send("33I%1d" % board)
        return x

    def setFil2(self, chan):
        board = self.params[chan][2] + 1

        x, y = self.send("33I%1d" % board)
        return x

    def getFiliamentLit(self, chan):
        """
        Gets the lit filiament
        Returns 1 or 2 for filiament, -1 if there was an error        
        """
        board = self.params[chan][2] + 1

        x, y = self.send("34I%1d" % board)
        if not x:
            return False, 0
        else:
            try:
                x = int(y)
            except:
                logging.warning("getFiliamentLit() : Error converting to int")
                return False, 0
        
        return True, x

    def readDegas(self, chan):
        board = self.params[chan][2] + 1
        x, y = self.send("42I%1d" % board)
        if not x:
            return False, False
        try:
            i = int(y)
        except:
            logging.critical("readDegas() : Unable to convert number.")
            return False, False

        return True, i
        
    def setDegas(self, chan, on = True):
        board = self.params[chan][2]

        if on:
            s = "41I%1d" % (board + 1)
        else:
            s = "40I%1d" % (board + 1)
            
        x, y = self.send(s)
        if not x:
            return False
        else:
            return True

    def send(self ,s):
        if not self.sendcommand(s):
            return False, ""
        else:
            x, y = self.readcommand()
            return x, y

    def readcommand(self):
        if self.mode == self.SERIAL:
            s = ""
            r = self.commport.read()
            while ord(r) != 13:
                s = s + r
                try:
                    r = self.commport.read()
                except:
                    logging.critical("readcommand() : error reading from serial interface")
                    return False, ""
        
        elif self.mode == self.SOCKET:
            try:
                s = self.commport.recv(1024)
            except:
                logging.critical("readcommand() : error reading from socket.")
                return False, ""
        
        if len(s) < 2:
            logging.critical("readcommand() : mallformed reply.")
            return False, ""
        
        s = s[:-1]

        logging.debug("readcommand() : %s" % s)

        if s[0] == "?":
            # A real error
            logging.critical("readcommand() : invalid command.")
            return False, ""
        if s[0] != ">":
            logging.critical("readcommand() : mallformed reply.")
            return False, ""
        
        s = s[1:]
        return True, s
    
    def sendcommand(self, data):
        s = "#%02d%s%c" % (self.unit, data, 13)
        logging.debug("sendcommand() : %s" % s)
        if self.mode == self.SERIAL:
            try:
                self.commport.write(s)
            except:
                logging.critical("sendcommand() : Unable to send data")
                return False
            return True
        else:
            try:
                self.commport.sendall(s)
            except:
                logging.critical("sendcommand() : Unable to send data")
                return False
            return True

if __name__ == "__main__":
    vac = VarianMGVac(("localhost", 3000), VarianMGVac.SOCKET)
    vac.connect()
    vac.init()
    vac.update()
