#
# mksevision.py (c) Stuart B. Wilkins 2008
#
# $Id: objects.py 85 2009-01-04 20:48:14Z swilkins $
# $HeadURL: svn+ssh://solids/home/swilkins/.svnrepos/pyVacuum/pyVacuum/objects.py $
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

import threading
import socket, shlex, numpy
from objects import *

import logging as log
logging = log.getLogger(__name__)

socket.setdefaulttimeout(10)

class MKSRGAThread(threading.Thread):
    def __init__(self, name=None): 
        threading.Thread.__init__(self, target=self.run, name=name, args=()) 
        self.run() 
    
    def run(self): 
        while 1: 

class MKSRGA(VacObject):
    def __init__(self, 
                 host = ("localhost", 10014), 
                 serial = None):
        
        VacObject.__init__(self)

        self.host = host
        self.serial = serial
    
        self.status = self.ERROR
        self.statusMessage = ""

        self.scanData = numpy.array([])
        self.zeroData = numpy.array([])

        self.measurementName = 'Analog1'
        self.params = [2, 100, 32, 2]
        self.initialized = False
        self.currentMass = 0.0
        self.infoDict = {}

    def getActions(self, chan):
        dict = { "ON" : self.ON,
                 "OFF" : self.OFF }
        return dict

    def setStatus(self, chan, status):
        if status == self.ON:
            self.setFilament(True)
        elif status == self.OFF:
            self.setFilament(False)
        return True

    def getMassRange(self):
        return self.params[0:2]

    def init(self):
        """ 
        Initializes the RGA 
        
        """
        logging.debug("init() : Started")
        if not self.open():
            logging.warning("init() : Failed to open comms")
            return False
        if not self.serial:
            logging.debug("init() : Reading Sensors")
            a, b = self.readSensors()
            if not a: 
                return False
            self.serial = b[0]
            logging.debug("init() : Set serial %s", self.serial)
        else:
            logging.debug("init() : Serial %s", self.serial)

        if not self.setSensor(self.serial):
            return False
        
        logging.debug("init() : Reading sensor info")
        if not self.getInfo():
            return False

        self.initialized = True
        return True

    def update(self):
        if not self.getFilament():
            return False
        if not self.getReading():
            return False
        return True

    def getData(self):
        return self.scanData

    def getZeroData(self):
        return self.zeroData

    def getValue(self, unit):
        return 0.0
    
    def getCurrentMass(self):
        return self.currentMass

    def getReading(self):
        if not self.getControl():
            return False
        if not self.setMeasurement():
            return False
        if not self.doMeasurement():
            return False
        return self.giveupControl()

    def doMeasurement(self):
        lastMass = self.params[1] + ((self.params[2] / 2) - 1) / float(self.params[2])
        logging.debug("lastmass = %f" % lastMass)
        if not self.sendCommand("ScanStart 1"):
            logging.warning("doMeasurement() : Failed to start scan")
            return False

        self.zeroData = numpy.array([])

        while 1:
            try:
                r = self.sock.recv(4096)
            except:
                logging.warning("doMeasurement() : Failed to read from socket")
                return False

            lines = r.splitlines()
            for line in lines:
                if line != '':
                    s = line.split()
                    if s[0] == "ZeroReading":
                        try:
                            self.zeroData = numpy.array((float(s[1]), float(s[2])))
                        except:
                            logging.warning("doMeasurement() : Failed to convert to float")
                        else:
                            logging.debug("doMeasurement() : bgnd = %e" % self.zeroData[1])
                            
                    if s[0] == "MassReading":
                        try:
                            x = float(s[1])
                            y = float(s[2])
                        except:
                            logging.warning("doMeasurement() : Failed to convert to float")
                        self.currentMass = x
                        logging.debug("x = %f y = %e" % (x, y))
                        if self.scanData.shape == (0,):
                            self.scanData = numpy.array([[x,y]])
                        else:
                            if (self.scanData[:,0] == x).sum():
                                self.scanData[(self.scanData[:,0] == x),1] = y
                            else:
                                self.scanData = numpy.vstack((self.scanData, 
                                                              numpy.array((x,y))))
                        if x == lastMass:
                            logging.debug("doMeasurement() : End of reading")
                            self.currentMass = 0.0
                            return True
        return True

    def setMeasurement(self):
        a, b = self.sendCommand("AddAnalog %s %d %d %d %d 0 0 1" %
                                (self.measurementName,
                                 self.params[0], self.params[1], 
                                 self.params[2], self.params[3]))
         if not a:
            return False

        a, b = self.sendCommand("ScanAdd %s" % self.measurementName)
        return a

    def getInfo(self):
        a, infoDict = self.sendCommand("Info")
        if not a:
            return False

        for x in infoDict:
            logging.info("getInfo() : %s = %s" % (x, infoDict[x]))

        self.infoDict = infoDict

        return True

    def setFilament(self, onoff):
        if onoff:
            state = "On"
        else:
            state = "Off"

        a, b = self.sendCommand("FilamentControl %s" % state)
        if not a:
            return False
        return True

    def getFilament(self):
        a, b = self.sendCommand("FilamentInfo")
        if not a:
            return False

        self.filnumber = b['ActiveFilament']
        if b['SummaryState'][0] == "ON":
            self.status = self.ON
        elif b['SummaryState'][0] == "OFF":
            self.status = self.OFF  
        else:
            self.status = self.ERROR

        try:
            fil = int(b['ActiveFilament'][0])
        except:
            logging.warning("Failed to get filament status")
            return False
        
        self.statusMessage = "Filament %d" % fil
        
        return True

    def getStatus(self, unit):
        return self.status

    def getStatusMessage(self, unit):
        return self.statusMessage

    def getControl(self):
        a, b = self.sendCommand("Control %s %s" % ("pyVacuum", "0.1"))
        return a
    
    def giveupControl(self):
        a,b = self.sendCommand("Release")
        return a

    def setSensor(self, serial):
        a, b = self.sendCommand("Select %s" % serial)
        if not a:
            return False
        return True

    def readSensors(self):
        a, r = self.sendCommand("Sensors", dict = False)
        if not a:
            return False
        
        lines = r.splitlines()
        if len(lines) < 3:
            return False

        ser = []
        for l in lines[2:]:
            ser.append(l.split()[1])

        return True, ser

    def open(self):
        # Open a socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(self.host)
        except:
            logging.warn("Connect to %s:%d failed." % self.host)
            return False

        r = self.readCommand()
        print r
        if r is "":
            return False
        else:
            if r.splitlines()[0][0:6] != "MKSRGA":
                logging.warn("open() : Failed to receive handshake")
                return False
            
        return True

    def close(self):
        self.sock.close()

    def send(self, command):
        try:
            self.sock.sendall(command + "\n")
        except:
            logging.warn("Unable to send command %s.", command)
            return False
        logging.debug("send() : %s", command)
        return True
        
    def sendCommand(self, command, dict = True):

        if not self.send(command):
            return False, ""
        
        while 1:
            r = self.readCommand()
            if r == "":
                logging.debug("sendCommand() : failed to get reply")
                return False, ""
    
            lines = r.splitlines()
            params = lines[0].split()

            # Now we check if the async commands have been read!

            if params[0] == command.split()[0]:
                break
            else:
                logging.debug("sendCommand() : Async %s", r)

        d = {}
        if len(params) == 2:
            if (params[1] == "OK"):
                if not dict:
                    return True, r

                for s in lines[1:]:
                    logging.debug("sendCommand() : %s : %s" % (command, s))
                    if dict:
                        a = shlex.split(s)
                        d[a[0]] = a[1:]
                return True, d
        
        logging.debug("sendCommand() : bad command %s", r)
        return False, ""

    def readCommand(self):
        buffer = ""
        try:
            r = self.sock.recv(4096)
        except:
            return ""
        #logging.debug("readCommand() : %s", 
        #              r.replace('\n',':').replace('\r',''))
        d = {}
        while (r != ""):
            buffer = buffer + r
            if (buffer[-2] == chr(13)) and (buffer[-1] == chr(13)):
                return buffer[0:-5]
            r = self.sock.recv(4096)
        return ""

if __name__ == "__main__":

    rga = MKSRGA(host = ("localhost", 10014),
                 serial = None)

    rga.init()
    rga.getReading()
    rga.close()
