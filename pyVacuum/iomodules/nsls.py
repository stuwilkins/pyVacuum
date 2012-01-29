#
# nsls.py (c) Stuart B. Wilkins 2008
#
# $Id: nsls.py 126 2009-11-01 16:07:42Z swilkins $
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
import httplib
import urllib

from objects import *

from ..log import setupLog
logging = setupLog(__name__)

import sgmllib

class NSLSParser(sgmllib.SGMLParser):
    "A simple parser class."

    def parse(self, s):
        "Parse the given string 's'."
        self.feed(s)
        self.close()

    def __init__(self, verbose=0):
        "Initialise an object, passing 'verbose' to the superclass."

        sgmllib.SGMLParser.__init__(self, verbose)
        
        self.intd = False
        self.message = []

    def start_td(self, attributes):
        self.intd = True
        
    def end_td(self):
        self.intd = False

    def handle_data(self, data):
        if self.intd:
            s = data.strip()
            if len(s):
                self.message.append(s)

    def get_message(self):
        return '\n'.join(self.message[2:])
            

class NSLSChan2:
    def __init__(self, host = None, url = None):
        if host is None:
            self.host = ("status.nsls.bnl.gov", 80)
        else:
            self.host = host

        if url is None:
            self.url = "/cgi-bin/web_ch2_beaminfo.pl"
        else:
            self.url = url

    def getMessage(self):
        u = "http://%s:%d/%s" % (self.host[0], self.host[1], self.url)

        h = httplib.HTTPConnection(self.host[0], self.host[1])
        h.request("GET", "/%s" % self.url)
        r = h.getresponse()
        if r.status != 200:
            logging.warning("Failed to connect to %s reason = %s" %
                            (self.host, r.reason)) 
            return (False, 0.0)
        
        text = r.read()
        p = NSLSParser()
        p.parse(text)
        return True, p.get_message()
  

class NSLSDeviceReadings:
    
    XAVAIL = 0
    UAVAIL = 1
    UVCURR = 2
    XRCURR = 3
    XRLIFE = 4
    X1GAP  = 5
    XRMESS = 6

    PAGES = { XAVAIL : "Status/Readback/xbeamavail",
              UAVAIL : "Status/Readback/ubeamavail",
              UVCURR : "Status/Readback/uvcurr",
              XRCURR : "Status/Readback/xrcurr",
              XRLIFE : "Status/Readback/xrlftime",
              X1GAP  : "Status/Readback/xsxugap",
              XRMESS : "Status/Readback/xrmsg"}

    def __init__(self, host = None):
        if host is None:
            self.host = ("status.nsls.bnl.gov", 80)
        else:
            self.host = host

    def getReading(self, type):
        h = httplib.HTTPConnection(self.host[0], self.host[1])
        h.request("GET", "/%s" % self.PAGES[type])
        r = h.getresponse()
        if r.status != 200:
            logging.warning("Failed to connect to %s reason = %s" %
                            (self.host, r.reason)) 
            return (False, 0.0)

        s = r.read().splitlines()
        
        if type < 6:
            try:
                val = float(s[0])
            except:
                logging.warning("Failed to convert float to value")
                return (False, 0.0)

            return (True, val)
        else:
            return (True, s[0].strip())

class NSLSRingChannel2(VacObject):
    def __init__(self, host = None):
        VacObject.__init__(self)
        self.chan2 = NSLSChan2(host = ('130.199.195.17',80))
        self.status = self.ERROR
    def update(self):
        a,b = self.chan2.getMessage()
        if a == True:
            self.status = self.ON
            self.statusMessage = b
        else:
            self.status = self.OFF
        #self.emitCallback()

    def getUnits(self, unit):
        return ""

    def getStatus(self, unit):
        return self.status

    def getStatusMessage(self, unit):
        return self.statusMessage

    def getValue(self, unit):
        return 0.0
        
class NSLSRingStatus(VacObject):
    def __init__(self, ring = "XRAY", host = None):
        VacObject.__init__(self)
        self.status = self.OFF
        self.NSLS = NSLSDeviceReadings(host)
        self.value = [0.0, 0.0, 0.0]
        self.status = self.OFF
        self.statusMessage = ""

    def update(self):
        b, r = self.NSLS.getReading(NSLSDeviceReadings.XAVAIL)
        if b == True:
            if r == 0:
                self.status = self.OFF
            else:
                self.status = self.ON
        else:
            self.status = self.ERROR

        b, r = self.NSLS.getReading(NSLSDeviceReadings.XRCURR)
        if b == True:
            self.value[0] = r
        else:
            self.status = self.ERROR

        b, r = self.NSLS.getReading(NSLSDeviceReadings.XRLIFE)
        if b == True:
            self.value[1] = r
        else:
            self.status = self.ERROR

        b, r = self.NSLS.getReading(NSLSDeviceReadings.X1GAP)
        if b == True:
            self.value[2] = r
        else:
            self.status = self.ERROR

        b, r = self.NSLS.getReading(NSLSDeviceReadings.XRMESS)
        if b == True:
            self.statusMessage = r
        else:
            self.status = self.ERROR
        
        #self.emitCallback()
        return True

    def getUnits(self, unit):
        if unit == 0:
            return "mA"
        else:
            return "mA.s^-1"

    def getStatus(self, unit):
        return self.status

    def getStatusMessage(self, unit):
        return self.statusMessage

    def getValue(self, unit):
        return self.value[unit]

if __name__ == "__main__":
    # Do a test
    
    a = NSLSDeviceReadings()
    print a.getReading(NSLSDeviceReadings.XRMESS)

    #b = NSLSChan2(host = ('130.199.195.17',80))
    #print b.getMessage()
    
    

#    
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/iomodules/nsls.py $
#
