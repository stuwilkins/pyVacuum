#
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

from modbus import *
from objects import *

import logging as log
logging = log.getLogger(__name__)

import cothread
import cothread.catools as catools

class EpicsGauge(VacObject):
    def __init__(self, pvName = [None], gaugeType = "ION"):
        VacObject.__init__(self)

        self.pvName = pvName
        self.pvNameEmission = [p + ":ctl:emission:fbk" for p in pvName]
        self.pvNameDegas = [p + ":ctl:degas:fbk" for p in pvName]

        self.gaugeType = gaugeType

        self.pressures = []
        self.status = []
        self.statusMessage = []
        for n in self.pvName:
            self.pressures.append(-1.0)
            self.status.append(self.ERROR)
            self.statusMessage.append("")

        self.units = "None"

        self.initialized = False
        self.needsPolling = False

    def init(self):
        self.initialized = True

        # Setup callbacks for EPICS PVs
        self.subVal = catools.camonitor(self.pvName, self.updateCallback)

        if (self.gaugeType == "ION") or (self.gaugeType == "PENG"):
            self.subEmission = catools.camonitor(self.pvNameEmission, 
                                                 self.updateEmissionCallback,
                                                 format=catools.FORMAT_CTRL,
                                                 notify_disconnect=True)
        if self.gaugeType == "ION":
            self.subDegas = catools.camonitor(self.pvNameDegas, 
                                              self.updateDegasCallback,
                                              format=catools.FORMAT_CTRL,
                                              notify_disconnect=True)
        return True

    def getActions(self, chan):
        
        if self.gaugeType[chan] == "ION":
            dict = {"ON"       : self.ON,
                    "OFF"      : self.OFF,
                    "DEGAS"    : self.DEGAS,
                    "SWAP FIL" : self.SWAPFILL}
        elif self.gaugeType[chan] == "PENG":
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

    def update(self):
        # For EPICS we set callbacks so we dont need to update!
        return

    def getStatus(self, unit):
        return self.status[unit]

    def setStatus(self, unit, status):
        # Here we just write to PVs
        if status == self.ON:
            catools.caput(self.pvName[unit] + ":ctl:emission", "ON")
        elif status == self.OFF:
            catools.caput(self.pvName[unit] + ":ctl:emission", "OFF")
        elif status == self.DEGAS:
            catools.caput(self.pvName[unit] + ":ctl:degas", "ON")
        else:
            return False
        return True

    def getValue(self, unit):
        return self.pressures[unit]

class EpicsValve(VacObject):
    def __init__(self, pvName = [None]):
        VacObject.__init__(self)

        self.ipaddr = [i + ":status" for i in pvName];
        self.opaddr = pvName
        self.fbkaddr = [i + ":fbk" for i in pvName];
       
        self.status = [self.ERROR for i in self.opaddr]

        for n in self.opaddr:
            self.status.append(self.ERROR)

        self.initialized = False
        self.needsPolling = False

    def init(self):
        self.initialized = True

        # Setup callbacks for EPICS PVs
        self.sub = catools.camonitor(self.ipaddr, self.updateCallback, 
                                     format=catools.FORMAT_CTRL,
                                     notify_disconnect=True)
        
        return True

    def getActions(self, chan):
        dict = { "OPEN" : self.OPEN,
                 "CLOSE" : self.CLOSE }
        return dict

    def updateCallback(self, val, index):
        # Used for epics callbacks
        if val.ok == False:
            self.status[index] = self.ERROR
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
            
    def update(self):
        # For python we set callbacks so we dont need to update!
        return True

    def getStatus(self, unit):
        # Get two bits for valve status
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

class EpicsIonPump(VacObject):
    GaugeStart = 16
    MaxChan = 16
    def __init__(self, pvName = None):
        VacObject.__init__(self)

        self.pvName = pvName
        self.pvNameCurrent = [i + ":current" for i in pvName]
        self.pvNameVoltage = [i + ":voltage" for i in pvName]
        self.pvNamePressure = [i + ":pressure" for i in pvName]
        self.pvNameStatus = [i + ":status" for i in pvName]
        self.pvNameOnOff = [i + ":ctl:onoff" for i in pvName]

        self.pressures = []
        self.pressuresUnits = []
        self.currents = []
        self.currentsUnits = []
        self.voltages = []
        self.voltagesUnits = []
        self.status = []
        self.statusMessage = []
        for i in range(self.MaxChan):
            self.pressures.append(0.0)
            self.currents.append(0.0)
            self.voltages.append(0.0)
            self.voltagesUnits.append("None")
            self.pressuresUnits.append("None")
            self.currentsUnits.append("None")
            self.status.append(self.ERROR)
            self.statusMessage.append("")

        self.needsPolling = False

    def init(self):
        self.initialized = False
        self.subValCurrent = catools.camonitor(self.pvNameCurrent, self.updateCurrentCallback,
                                               notify_disconnect=True)
        self.subValVoltage = catools.camonitor(self.pvNameVoltage, self.updateVoltageCallback,
                                               notify_disconnect=True)
        self.subValPressure = catools.camonitor(self.pvNamePressure, self.updatePressureCallback,
                                                notify_disconnect=True)
        self.subValStatus = catools.camonitor(self.pvNameStatus, self.updateStatusCallback,
                                              format=catools.FORMAT_CTRL,notify_disconnect=True)
        self.subValOnOff = catools.camonitor(self.pvNameOnOff, self.updateOnOffCallback,
                                              format=catools.FORMAT_CTRL,notify_disconnect=True)
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

    def update(self):
        return True

    def setStatus(self, unit, status):
        # Here we just write to PVs
        if status == self.ON:
            catools.caput(self.pvName[unit] + ":ctl:onoff", "ON")
        elif status == self.OFF:
            catools.caput(self.pvName[unit] + ":ctl:onoff", "OFF")
        else:
            return False
        return True

class EpicsSwitch(VacObject):
    def __init__(self, pvName = [None]):
        VacObject.__init__(self)

        self.opaddr = pvName
        self.fbkaddr = [i + ":fbk" for i in pvName];
       
        self.status = [self.ERROR for i in self.opaddr]

        for n in self.opaddr:
            self.status.append(self.ERROR)

        self.initialized = False
        self.needsPolling = False

    def init(self):
        self.initialized = True

        # Setup callbacks for EPICS PVs
        self.sub = catools.camonitor(self.fbkaddr, self.updateCallback, 
                                     format=catools.FORMAT_CTRL,
                                     notify_disconnect=True)
        
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
            
    def update(self):
        # For python we set callbacks so we dont need to update!
        return True

    def getStatus(self, unit):
        # Get two bits for valve status
        return self.status[unit]

    def setStatus(self, unit, status):
        # Here we just write to PV

        if status == self.ON:
            s = catools.caput(self.opaddr[unit], "ON")
        elif status == self.OFF:
            s = catools.caput(self.opaddr[unit], "OFF")
        else:
            return False

        if not s:
            return False
        
        return True

    def getValue(self, unit):
        if self.status[unit] == self.OPEN:
            return 1
        else:
            return 0
