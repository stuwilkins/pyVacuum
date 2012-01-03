
# epics.py (c) Stuart B. Wilkins 2008
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

from objects import *

import logging as log
logging = log.getLogger(__name__)
logging.setLevel(log.DEBUG)
ch = log.StreamHandler()
ch.setLevel(log.DEBUG)
formatter = log.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logging.addHandler(ch)


import cothread
import cothread.catools as catools

class EpicsBase(VacObject):
    def __init__(self):
        VacObject.__init__(self)
        self.epicsSubscriptions = []
        self.needsPolling = False

    def getEpicsUnits(self,pvlist):
        u = []
        for n,pv in enumerate(pvlist):
            s, v = self.epicsGet(pv + ".EGU", "Unk")
            if not s:
                return False, ["Unk" for i in pvlist]
            u.append(v)
        return True, u 

    def addEpicsCallback(self,pv,callback):
        s = catools.camonitor(pv,callback, 
                              format=catools.FORMAT_CTRL,
                              notify_disconnect=True)
        if type(s) == list:
            self.epicsSubscriptions += s
        else:
            self.epicsSubscriptions.append(s) 

    def closeAllEpicsCallbacks(self):
        for s in self.epicsSubscriptions:
            s.close()

        return True

    def epicsGet(self, pv, default):
        try:
            s = catools.caget(pv)
        except cothread.Timedout:
            return False, default
        return True, s

    def epicsPut(self, pv, val):
        try:
            s = catools.caput(pv, val)
        except cothread.Timedout:
            return False
        return True

    def close(self):
        self.closeAllEpicsCallbacks()
        return True

    def update(self):
        # For EPICS we set callbacks so we dont need to update!
        return True

    def getStatus(self, unit):
        return self.status[unit]

    def hasValue(self, unit):
        return True


class EpicsGauge(EpicsBase):
    def __init__(self, pvName = [None], gaugeType = "ION"):
        EpicsBase.__init__(self)

        self.pvName = pvName
        self.pvNameEmission = [p + ":ctl:emission:fbk" for p in pvName]
        self.pvNameDegas = [p + ":ctl:degas:fbk" for p in pvName]

        self.gaugeType = gaugeType

        self.pressures = []
        self.status = []
        self.statusMessage = []
        self.units = []
        for n in self.pvName:
            self.pressures.append(-1.0)
            self.status.append(self.ERROR)
            self.statusMessage.append("")
            self.units.append("Undef")

        self.initialized = False
        self.needsPolling = False

    def init(self):
        self.initialized = False
        s, self.units = self.getEpicsUnits(self.pvName)

        # Setup callbacks for EPICS PVs

        self.addEpicsCallback(self.pvName, self.updateCallback)
        if (self.gaugeType == "ION") or (self.gaugeType == "PENG"):
            self.addEpicsCallback(self.pvNameEmission, self.updateEmissionCallback)
        if self.gaugeType == "ION":
            self.addEpicsCallback(self.pvNameDegas, self.updateDegasCallback)
        
        self.initialized = True
        return True

    def getActions(self, chan):
        if self.gaugeType == "ION":
            dict = {"ON"       : self.ON,
                    "OFF"      : self.OFF,
                    "DEGAS"    : self.DEGAS,
                    "SWAP FIL" : self.SWAPFILL}
        elif self.gaugeType == "PENG":
            dict = { "ON"       : self.ON,
                     "OFF"      : self.OFF }
        else:
            dict = {}

        return dict

    def updateCallback(self, val, index):
        # Used for epics callbacks
        if val.ok == False:
            self.status[index] = self.ERROR
        else:
            if self.gaugeType == "PIRG":
                self.status[index] = self.ON
            self.pressures[index] = val            
        return

    def updateEmissionCallback(self, val, index):
        if val.ok == False:
            self.status[index] = self.ERROR
            return

        if val.enums[val] == "ON":
            self.status[index] = self.ON
        elif val.enums[val] == "OFF":
            self.status[index] = self.OFF
        else:
            self.status[index] = self.ERROR
        return

    def updateDegasCallback(self, val, index):
        if val.ok == False:
            self.status[index] = self.ERROR
            return 
        return

    def setStatus(self, unit, status):
        # Here we just write to PVs
        if status == self.ON:
            s = self.epicsPut(self.pvName[unit] + ":ctl:emission", "ON")
        elif status == self.OFF:
            s = self.epicsPut(self.pvName[unit] + ":ctl:emission", "OFF")
        elif status == self.DEGAS:
            s = self.epicsPut(self.pvName[unit] + ":ctl:degas", "ON")
        else:
            return False
        return s

    def getValue(self, unit):
        return self.pressures[unit]

    def getUnits(self, unit):
        return self.units[unit]

class EpicsValve(EpicsBase):
    def __init__(self, pvName = [None]):
        EpicsBase.__init__(self)

        self.ipaddr = [i + ":status" for i in pvName];
        self.opaddr = pvName
        self.fbkaddr = [i + ":fbk" for i in pvName];
       
        self.status = [self.ERROR for i in self.opaddr]
        self.statusfbk = [self.ERROR for i in self.opaddr]

        for n in self.opaddr:
            self.status.append(self.ERROR)

        self.initialized = False

    def init(self):
        self.initialized = True

        # Setup callbacks for EPICS PVs
        s = self.addEpicsCallback(self.ipaddr, self.updateCallback)
        s = self.addEpicsCallback(self.fbkaddr, self.updateFbkCallback)
        return True

    def getActions(self, chan):
        dict = { "OPEN" : self.OPEN,
                 "CLOSE" : self.CLOSE }
        return dict

    def updateCallback(self, val, index):
        # Used for epics callbacks
        if val.ok == False:
            self.status[index] = self.ERROR
            logging.debug("Update for %s failed", val.name)
            return

        enum = val.enums
        newstate = enum[val]
        if newstate == "OPEN":
            self.status[index] = self.OPEN
        elif newstate == "CLOSED":
            self.status[index] = self.CLOSE
        else:
            self.status[index] = self.ERROR            
        return

    def updateFbkCallback(self, val, index):
        if val.ok == False:
            self.status[index] = self.ERROR
            logging.warn("Update for %s failed", val.name)
            return
        enum = val.enums
        newstate = enum[val]
        if newstate == "OPEN":
            self.statusfbk[index] = self.OPEN
        elif newstate == "CLOSE":
            self.statusfbk[index] = self.CLOSE
        else:
            self.statusfbk[index] = self.ERROR            
        return

    def getStatus(self, unit):
        if self.statusfbk[unit] != self.status[unit]:
            return self.FAULT
        else:
            return self.status[unit]
            
    def setStatus(self, unit, status):
        # Here we just write to PV

        if status == self.OPEN:
            s = catools.caput(self.opaddr[unit], "OPEN")
        elif status == self.CLOSE:
            s = catools.caput(self.opaddr[unit], "CLOSE")
        else:
            return False

        if not s:
            return False
        else:
            return    

    def getValue(self, unit):
        if self.status[unit] == self.OPEN:
            return 1
        else:
            return 0

class EpicsIonPump(EpicsBase):
    GaugeStart = 16
    MaxChan = 16
    def __init__(self, pvName = None):
        EpicsBase.__init__(self)

        self.pvName = pvName
        self.pvNameCurrent = [i + ":current" for i in pvName]
        self.pvNameVoltage = [i + ":voltage" for i in pvName]
        self.pvNamePressure = [i + ":pressure" for i in pvName]
        self.pvNameStatus = [i + ":status" for i in pvName]
        self.pvNameOnOff = [i + ":ctl:onoff" for i in pvName]

        self.pressures = [0.0 for i in pvName]
        self.pressuresUnits = ["Unk" for i in pvName]
        self.currents = [0.0 for i in pvName]
        self.currentsUnits = ["Unk" for i in pvName]
        self.voltages = [0.0 for i in pvName]
        self.voltagesUnits = ["Unk" for i in pvName]
        self.status = [self.ERROR for i in pvName]
        self.statusMessage = ["ERROR" for i in pvName]

        self.needsPolling = False

    def init(self):
        self.initialized = False

        s, self.pressuresUnits = self.getEpicsUnits(self.pvNamePressure)
        s, self.voltagesUnits = self.getEpicsUnits(self.pvNameVoltage)
        s, self.currentsUnits = self.getEpicsUnits(self.pvNameCurrent)

        self.addEpicsCallback(self.pvNameCurrent, self.updateCurrentCallback)
        self.addEpicsCallback(self.pvNameVoltage, self.updateVoltageCallback)
        self.addEpicsCallback(self.pvNamePressure, self.updatePressureCallback)
        self.addEpicsCallback(self.pvNameStatus, self.updateStatusCallback)
        self.addEpicsCallback(self.pvNameOnOff, self.updateOnOffCallback)

        self.initialized = True
        return True

    def updateOnOffCallback(self, val, index):
        if val.ok:
            if val.enums[val] == "ON":
                self.status[index] = self.ON
            elif val.enums[val] == "OFF":
                self.status[index] = self.OFF
            else:
                self.status[index] = self.ERROR
        else:
            self.status[index] = self.ERROR

    def updateVoltageCallback(self, val, index):
        if val.ok == True:
            self.voltages[index] = val
        else:
            self.status[index] = self.ERROR

    def updateCurrentCallback(self, val, index):
        if val.ok == True:
            self.currents[index] = val
        else:
            self.status[index] = self.ERROR

    def updatePressureCallback(self, val, index):
        if val.ok == True:
            self.pressures[index] = val
        else:
            self.status[index] = self.ERROR

    def updateStatusCallback(self, val, index):
        if val.ok == True:
            self.status[index] = self.ON
            self.statusMessage[index] = val.enums[val]
        else:
            self.status[index] = self.ERROR

    def getActions(self, chan):
        if chan < self.GaugeStart:
            dict = { "ON" : self.ON ,
                     "OFF" : self.OFF }
        else:
            dict = {}
        
        return dict
    
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
    def setStatus(self, unit, status):
        # Here we just write to PVs
        if status == self.ON:
            s = self.epicsPut(self.pvName[unit] + ":ctl:onoff", "ON")
        elif status == self.OFF:
            s = self.epicsPut(self.pvName[unit] + ":ctl:onoff", "OFF")
        else:
            return False
        return s

class EpicsSwitch(EpicsBase):
    def __init__(self, pvName = [None]):
        EpicsBase.__init__(self)

        self.opaddr = pvName
        self.fbkaddr = [i + ":fbk" for i in pvName];
       
        self.status = [self.ERROR for i in self.opaddr]

        for n in self.opaddr:
            self.status.append(self.ERROR)

        self.initialized = False
        self.needsPolling = False

    def init(self):
        # Setup callbacks for EPICS PVs
        self.addEpicsCallback(self.fbkaddr, self.updateCallback)
        self.initialized = True
        return True

    def getActions(self, chan):
        dict = { "ON" : self.ON,
                 "OFF" : self.OFF }
        return dict

    def updateCallback(self, val, index):
        # Used for epics callbacks
        if val.ok == False:
            self.status[index] = self.ERROR
            return

        enum = val.enums
        newstate = enum[val]
        if newstate == "ON":
            self.status[index] = self.ON
        elif newstate == "OFF":
            self.status[index] = self.OFF
        else:
            self.status[index] = self.ERROR            
        return
            
    def setStatus(self, unit, status):
        # Here we just write to PV

        if status == self.ON:
            s = self.epicsPut(self.opaddr[unit], "ON")
        elif status == self.OFF:
            s = self.epicsPut(self.opaddr[unit], "OFF")
        else:
            return False

        if not s:
            return False
        
        return True

    def getValue(self, unit):
        if self.status[unit] == self.ON:
            return 1
        else:
            return 0

    
class EpicsPV(EpicsBase):
    def __init__(self, pvName = [None]):
        EpicsBase.__init__(self)

        self.ipaddr = pvName
        
        self.status = [self.ERROR for i in self.ipaddr]
        self.value = [0.0 for i in self.ipaddr]
        self.statusText = ["" for i in self.ipaddr]

        self.initialized = False

    def init(self):
        # Setup callbacks for EPICS PVs
        self.initialized = False
        s, u = self.getEpicsUnits(self.ipaddr)
        if not s:
            return False
        self.units = u

        self.addEpicsCallback(self.ipaddr, self.updateCallback)
        
        self.initialized = True
        return True

    def updateCallback(self, val, index):
        # Used for epics callbacks
        if val.ok == False:
            self.status[index] = self.ERROR
            return
        
        if hasattr(val, "enums"):
            enum = val.enums
            val = enum[val]
        
        self.status[index] = self.ON
        self.value[index] = val
       
        return True

    def getValue(self, unit):
        if self.status[unit] == self.ON:
            return self.value[unit]
        else:
            return 0

class EpicsTurbo(EpicsBase):
    def __init__(self, pvName = [None]):
        EpicsBase.__init__(self)

        self.statusaddr = [i + ":status" for i in pvName]
        self.opaddr = [i + ":onoff" for i in pvName]
        self.fbkaddr = [i + ":onoff:fbk" for i in pvName]
       
        self.status = [self.ERROR for i in self.opaddr]
        self.statusText = ["" for i in self.opaddr]

        self.initialized = False

    def init(self):
        # Setup callbacks for EPICS PVs
        #self.addEpicsCallback(self.fbkaddr, self.updateCallback)
        self.addEpicsCallback(self.statusaddr, self.updateStatusCallback)
        self.initialized = True
        return True

    def getActions(self, chan):
        dict = { "ON" : self.ON,
                 "OFF" : self.OFF }
        return dict

    def updateCallback(self, val, index):
        # Used for epics callbacks
        if val.ok == False:
            self.status[index] = self.ERROR
            return

        enum = val.enums
        newstate = enum[val]
        if newstate == "ON":
            self.status[index] = self.ON
        elif newstate == "OFF":
            self.status[index] = self.OFF
        else:
            self.status[index] = self.ERROR            
        return
            
    def updateStatusCallback(self, val, index):
        if val.ok == False:
            self.status[index] = self.ERROR
            return
        
        cmd = val.enums[val]
        print cmd
        if cmd == "ON":
            self.status[index] == self.ON
        elif cmd == "NO CONNECTION":
            self.status[index] = self.ERROR
        elif cmd == "ACCELERATING":
            self.status[index] = self.ACCEL
        elif cmd == "BRAKE":
            self.status[index] = self.BRAKE
        elif cmd == "FAULT":
            self.status[index] = self.FAULT
        else:
            self.status[index] = self.FAULT
            self.statusText[index] = val

        return

    def setStatus(self, unit, status):
        # Here we just write to PV

        if status == self.ON:
            s = self.epicsPut(self.opaddr[unit], "ON")
        elif status == self.OFF:
            s = self.epicsPut(self.opaddr[unit], "OFF")
        else:
            return False

        if not s:
            return False
        
        return True

    def getValue(self, unit):
        if self.status[unit] == self.ON:
            return 1
        else:
            return 0
    
