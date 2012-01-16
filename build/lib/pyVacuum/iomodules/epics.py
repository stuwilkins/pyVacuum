
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
from pyVacuum.log import setupLog

logging = setupLog(__name__)

import cothread
import cothread.catools as catools

import time

import numpy

class EpicsBase(VacObject):
    def __init__(self):
        """Initialize the object. Inherits from VacObject"""
        VacObject.__init__(self)
        self.epicsSubscriptions = []
        self.needsPolling = False
        self.autoActions = None

    def addActionsFromPV(self,pvListList, prefix = None):
        """Connect to controlling PV and set actions
        
        Note : pvListList must be a LIST of a list of pv's"""
 
        # Reorder the list (transpose in matrix language!
        pvListListT = zip(*pvListList)
        
        # Make dummy prefix
        if prefix is None:
            prefix = ['' for i in pvListList]
        
        allActions = []
        allPVs = []
        allResults = []

        for pvList in pvListListT:
            # This loops over all "units"
            result = catools.caget(pvList, throw = False, 
                                   format = catools.FORMAT_CTRL,
                                   timeout = 0.5) # Timeout short
            actiondict = {}
            actionpvs = []
            results = []
            flag = False
            i = 0 # Index has to be unique!
            # This loops over all PVs
            for val,p in zip(result, prefix):
                if val.ok:
                    if hasattr(val,"enums"):
                        for e in val.enums:
                            actiondict.update({p + e:i})
                            actionpvs.append([val.name, e])
                            i = i + 1
                            flag = True
                    else:
                        logging.error("addActionsFromPV() : BAD PV %s", val.name)
                else:
                    logging.warning("addActionsFromPV() : Unable to get actions for %s", val.name)
            allActions.append(actiondict)
            allPVs.append(actionpvs)
            allResults.append(flag)
        self.autoActions = {'actions' : allActions, 'PVs' : allPVs}

        return allResults

    def getActions(self, unit):
        if self.autoActions is None:
            return {}
        else:
            return self.autoActions['actions'][unit]

    def setStatus(self, unit, status):
        # Here we just write to PV
        if self.autoActions is None:
            return False

        val = self.autoActions['PVs'][unit][status]

        logging.debug("setStatus() : pv = %s status = %s", val[0], val[1])
        s = catools.caput(val[0],val[1])
        if not s:
            logging.error("setStatus() : Unable to set status on unit %d", unit)
            return False
        else:
            return True
   
    def addEpicsCallback(self,pv,callback):
        """Add PV callbacks and store the subscriptions"""
        s = catools.camonitor(pv,callback, 
                              format=catools.FORMAT_CTRL,
                              notify_disconnect=True)
        logging.info("addEpicsCallback() : Callback added for PV %s", pv)
        if type(s) == list:
            self.epicsSubscriptions += s
        else:
            self.epicsSubscriptions.append(s) 

    def closeAllEpicsCallbacks(self):
        """Close all EPICS subscriptions"""
        logging.debug("closeAllEpicsCallbacks() : closing callbacks")
        for s in self.epicsSubscriptions:
            s.close()

        return True

    def epicsGet(self, pv, default):
        """Do an epics caget and return value

        pv : string : process variable
        default : string : return this is there is an error"""
        s = catools.caget(pv, throw = False)
        if s.ok == False:
            logging.warning("Failed to get '%s' error = %s", s.name, str(s))
            return False, default
        return True, s

    def epicsPut(self, pv, val):
        """Do an epics caput and return status"""
        s = catools.caput(pv, val, throw = False)
        if not s:
            logging.warning("Failed caput on '%s' error = %s", s.name, str(s))
            return False
        return True

    def close(self):
        logging.debug("Closing EPICS callbacks")
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
        self.pvNameFbk = [p + ":fbk" for p in pvName]
        self.pvNameEmission = [p + ":ctl:emission:fbk" for p in pvName]
        self.pvNameEmissionCtl = [p + ":ctl:emission" for p in pvName]
        self.pvNameDegas = [p + ":ctl:degas:fbk" for p in pvName]
        self.pvNameDegasCtl = [p + ":ctl:degas" for p in pvName]

        self.gaugeType = gaugeType

        self.pressures = []
        self.status = []
        self.statusMessage = []
        self.units = []
        self.statusfbk = []
        for n in self.pvName:
            self.pressures.append(-1.0)
            self.status.append(self.ERROR)
            self.statusfbk.append(self.ERROR)
            self.statusMessage.append("")
            self.units.append("Undef")

        self.initialized = False
        self.needsPolling = False

    def init(self):
        self.initialized = False

        # Setup callbacks for EPICS PVs

        self.addActionsFromPV([self.pvNameEmissionCtl, self.pvNameDegasCtl],
                              ["Gauge ", "Degas "])
        self.addEpicsCallback(self.pvNameFbk, self.updateFbkCallback)
        self.addEpicsCallback(self.pvName, self.updateCallback)
        self.addEpicsCallback(self.pvNameEmission, self.updateEmissionCallback)
        self.addEpicsCallback(self.pvNameDegas, self.updateDegasCallback)
        
        self.initialized = True
        return True

    def getInformation(self, unit):
        text = ""
        text += "PV : %s\n" % self.pvName[unit]
        text += "\n"
        text += "Status = %s\n" % self.NICETEXT[self.status[unit]]
        text += "Feedback = %s\n" % self.NICETEXT[self.statusfbk[unit]]
        text += "Status Text = %s\n" % self.statusMessage[unit]
        text += "Pressure = %g\n" % self.pressures[unit]
        return "EPICS Controlled Guage", text 

    def updateFbkCallback(self, val, index):
        # Used for epics callbacks
        if val.ok == False:
            self.status[index] = self.ERROR
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
        else:
            if val.enums[val] == "ON":
                self.statusfbk[index] = self.ON
            elif val.enums[val] == "OFF":
                self.statusfbk[index] = self.OFF
            else:
                self.statusfbk[index] = self.ERROR

        self.emitCallback(unit = index)

    def updateCallback(self, val, index):
        # Used for epics callbacks
        if val.ok == False:
            self.status[index] = self.ERROR
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
        else:
            if self.gaugeType == "PIRG":
                self.status[index] = self.ON
            self.pressures[index] = val   
            self.units[index] = val.units
        
        self.emitCallback(unit = index)

    def updateEmissionCallback(self, val, index):
        if val.ok == False:
            self.status[index] = self.ERROR
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
        else:
            if val.enums[val] == "ON":
                self.status[index] = self.ON
            elif val.enums[val] == "OFF":
                self.status[index] = self.OFF
            else:
                self.status[index] = self.ERROR
        
        self.emitCallback(unit = index)

    def updateDegasCallback(self, val, index):
        if val.ok == False:
            self.status[index] = self.ERROR
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
        
        self.emitCallback(unit = index)

    def getValue(self, unit):
        return self.pressures[unit]

    def getUnits(self, unit):
        return self.units[unit]
    
    def getStatus(self,unit):
        if (self.status[unit] == self.ON) and (self.statusfbk[unit] == self.OFF):
            return self.ERROR
        if (self.status[unit] == self.OFF) and (self.statusfbk[unit] == self.ON):
            return self.ERROR
        return self.status[unit]

class EpicsValve(EpicsBase):
    def __init__(self, pvName = [None], control = None):
        EpicsBase.__init__(self)

        self.opaddr = pvName
         
        self.ipaddr = [i + ":status" for i in pvName]
        self.fbkaddr = [i + ":fbk" for i in pvName]
        self.valveCtrl = [False for i in pvName]
        self.status = [self.ERROR for i in self.opaddr]
        self.statusfbk = [self.ERROR for i in self.opaddr]
        self.statusText = ["" for i in self.opaddr]

    def init(self):
        self.initialized = True
        # Setup callbacks for EPICS PVs
        self.valveCtrl = self.addActionsFromPV([self.opaddr], ["Valve "])
        s = self.addEpicsCallback(self.ipaddr, self.updateCallback)
        s = self.addEpicsCallback(self.fbkaddr, self.updateFbkCallback)
        return True

    def getInformation(self, unit):
        text = ""
        text += "PV : %s" % self.opaddr[unit]
        text += "\n"
        text += "Status = %s\n" % self.NICETEXT[self.status[unit]]
        text += "Feedback = %s\n" % self.NICETEXT[self.statusfbk[unit]]
        text += "Status Text = %s\n" % self.statusText[unit]
        return "EPICS Controlled Valve", text 

    def updateCallback(self, val, index):
        # Used for epics callbacks
        if val.ok == False:
            self.status[index] = self.ERROR
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
        else:
            enum = val.enums
            newstate = enum[val]
            self.statusText[index] = newstate
            if newstate == "OPEN":
                self.status[index] = self.OPEN
            elif newstate == "CLOSED":
                self.status[index] = self.CLOSE
            else:
                self.status[index] = self.FAULT           
        self.emitCallback(unit = index)

    def updateFbkCallback(self, val, index):
        if val.ok == False:
            self.status[index] = self.ERROR
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
        else:
            enum = val.enums
            newstate = enum[val]
            if (newstate == "OPEN"):
                self.statusfbk[index] = self.OPEN
            elif newstate == "CLOSE":
                self.statusfbk[index] = self.CLOSE
            else:
                self.statusfbk[index] = self.FAULT           

        self.emitCallback(unit = index)

    def getStatus(self, unit):
        if self.valveCtrl[unit]:
            if self.statusfbk[unit] == self.status[unit]:
                return self.status[unit]
            else:
                return self.FAULT
        else:
            return self.status[unit]

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

        self.addActionsFromPV([self.pvNameOnOff], ['Pump '])

        self.addEpicsCallback(self.pvNameCurrent, self.updateCurrentCallback)
        self.addEpicsCallback(self.pvNameVoltage, self.updateVoltageCallback)
        self.addEpicsCallback(self.pvNamePressure, self.updatePressureCallback)
        self.addEpicsCallback(self.pvNameStatus, self.updateStatusCallback)
        self.addEpicsCallback(self.pvNameOnOff, self.updateOnOffCallback)

        self.initialized = True
        return True

    def getInformation(self, unit):
        if unit >= self.GaugeStart:
            newunit = unit - self.GaugeStart
        else:
            newunit = unit
        text = ""
        text += "PV : %s" % self.pvName[newunit]
        text += "\n"
        text += "Status = %s\n" % self.NICETEXT[self.status[newunit]]
        text += "Status Text = %s\n" % self.statusMessage[newunit]
        text += "Pressure = %g\n" % self.pressures[newunit]
        text += "Voltage = %f\n" % self.voltages[newunit]
        text += "Current = %g\n" % self.currents[newunit]
        return "EPICS Controlled IonPump", text 

    def updateOnOffCallback(self, val, index):
        if val.ok:
            if val.enums[val] == "ON":
                self.status[index] = self.ON
            elif val.enums[val] == "OFF":
                self.status[index] = self.OFF
            else:
                self.status[index] = self.ERROR
        else:
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
            self.status[index] = self.ERROR

    def updateVoltageCallback(self, val, index):
        if val.ok == True:
            self.voltages[index] = val
            self.voltagesUnits[index] = val.units
        else:
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
            self.status[index] = self.ERROR

        self.emitCallback(unit = index)

    def updateCurrentCallback(self, val, index):
        if val.ok == True:
            self.currents[index] = val
            self.currentsUnits[index] = val.units
        else:
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
            self.status[index] = self.ERROR

        self.emitCallback(unit = index)

    def updatePressureCallback(self, val, index):
        if val.ok == True:
            self.pressures[index] = val
            self.pressuresUnits[index] = val.units
        else:
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
            self.status[index] = self.ERROR

        self.emitCallback(unit = index)

    def updateStatusCallback(self, val, index):
        if val.ok == True:
            val = val.enums[val]
            if val == "STANDBY":
                self.status[index] = self.OFF
            elif val == "RUNNING":
                self.status[index] = self.ON
            else:
                self.status[index] = self.FAULT
            self.statusMessage[index] = val
            
        else:
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
            self.status[index] = self.ERROR
    
        self.emitCallback(unit = index)

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
            s = self.status[unit]
            return s  
        else:
            s = self.status[unit - self.GaugeStart]
            return s

    def getStatusMessage(self, unit):
        if unit < self.GaugeStart:
            return self.statusMessage[unit]
        else:
            return ""

    def getActions(self, unit):
        if unit >= self.GaugeStart:
            u = unit - self.GaugeStart
        else:
            u = unit

        return EpicsBase.getActions(self, u)
        

class EpicsSwitch(EpicsBase):
    def __init__(self, pvName = [None]):
        EpicsBase.__init__(self)

        self.opaddr = pvName
        self.fbkaddr = [i + ":fbk" for i in pvName];
       
        self.status = [self.ERROR for i in self.opaddr]
        self.statusMessage = ["Error" for i in self.opaddr]

        for n in self.opaddr:
            self.status.append(self.ERROR)

        self.initialized = False
        self.needsPolling = False

    def init(self):
        # Setup callbacks for EPICS PVs
        self.addActionsFromPV([self.opaddr])
        self.addEpicsCallback(self.fbkaddr, self.updateCallback)
        self.initialized = True
        return True

    def getInformation(self, unit):
        newunit = unit
        text = ""
        text += "PV : %s" % self.opaddr[newunit]
        text += "\n"
        text += "Status = %s\n" % self.NICETEXT[self.status[newunit]]
        text += "Status Text = %s\n" % self.statusMessage[newunit]
        return "EPICS Digital Switch", text

    def updateCallback(self, val, index):
        # Used for epics callbacks
        
        if val.ok == False:
            self.status[index] = self.ERROR
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
        else:
            if hasattr(val,'enums'):
                enum = val.enums
                newstate = enum[val]
                self.statusMessage[index] = newstate
            else:
                self.statusMessage[index] = ""
                self.status[index] = self.ERROR
                self.emitCallback(unit = index)
                return

            if newstate == "ON":
                self.status[index] = self.ON
            elif newstate == "OFF":
                self.status[index] = self.OFF
            else:
                # Default is that a good value means indicator is ON
                self.status[index] = self.ON            
        self.emitCallback(unit = index)

    def getValue(self, unit):
        if self.status[unit] == self.ON:
            return 1
        else:
            return 0

    def getStatusMessage(self, unit):
        return self.statusMessage[unit]

    
class EpicsPV(EpicsBase):
    def __init__(self, pvName = [None], pvNameOut = None):
        EpicsBase.__init__(self)
        self.ipaddr = pvName
        
        self.status = [self.ERROR for i in self.ipaddr]
        self.value = [0.0 for i in self.ipaddr]
        self.statusText = ["" for i in self.ipaddr]
        self.units = ["Unk" for i in self.ipaddr]

        if pvNameOut is None:
            self.isSettableValue = [False for i in pvName]
        else:
            self.isSettableValue = [(i is not None) for i in pvNameOut]
            self.opaddr = pvNameOut

        self.initialized = False

    def isSettable(self, chan):
        return self.isSettableValue[chan]

    def init(self):
        # Setup callbacks for EPICS PVs
        self.initialized = False
        self.addEpicsCallback(self.ipaddr, self.updateCallback)
        self.initialized = True
        return True

    def getInformation(self, unit):
        newunit = unit
        text = ""
        text += "PV : %s" % self.ipaddr[newunit]
        text += "\n"
        text += "Status = %s\n" % self.NICETEXT[self.status[newunit]]
        text += "Status Text = %s\n" % self.statusText[newunit]
        text += "Val = %s\n" % str(self.value[newunit])
        text += "Units = %s\n" % self.units[newunit]
        if self.isSettableValue[newunit]:
            text += "\nOutput PV : %s\n" % self.opaddr[newunit]
        return "EPICS PV Value", text

    def updateCallback(self, val, index):
        # Used for epics callbacks
        if val.ok == False:
            self.status[index] = self.ERROR
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
        else:
        
            if hasattr(val, "units"):
                self.units[index] = val.units

            if hasattr(val, "enums"):
                enum = val.enums
                self.statusText[index] = enum[val]
        
        self.status[index] = self.ON
        self.value[index] = val
        self.emitCallback(unit = index)

    def getValue(self, unit):
        if self.status[unit] == self.ON:
            return self.value[unit]
        else:
            return 0

    def setValue(self, unit, val):
        self.epicsPut(self.opaddr[unit], val)

    def getUnits(self, unit):
        return self.units[unit]

class EpicsTurbo(EpicsBase):
    def __init__(self, pvName = [None]):
        EpicsBase.__init__(self)

        self.statusaddr = [i + ":status" for i in pvName]
        self.opaddr = [i + ":onoff" for i in pvName]
        self.opaddrReset = [i + ":reset" for i in pvName]
        self.fbkaddr = [i + ":onoff:fbk" for i in pvName]
       
        self.status = [self.ERROR for i in self.opaddr]
        self.statusfbk = [self.ERROR for i in self.opaddr]
        self.statusText = ["Error" for i in self.opaddr]

        self.initialized = False

    def init(self):
        # Setup callbacks for EPICS PVs
        self.addActionsFromPV([self.opaddr, self.opaddrReset], ['Pump ', 'Reset '])
        self.addEpicsCallback(self.fbkaddr, self.updateCallback)
        self.addEpicsCallback(self.statusaddr, self.updateStatusCallback)
        self.initialized = True
        return True

    def getInformation(self, unit):
        newunit = unit
        text = ""
        text += "PV : %s" % self.opaddr[newunit]
        text += "\n"
        text += "Status = %s\n" % self.NICETEXT[self.status[newunit]]
        text += "Status Fbk = %s\n" % self.NICETEXT[self.statusfbk[newunit]]
        text += "Status Text = %s\n" % self.statusText[newunit]
        return "EPICS Turbo Pump", text

    def updateCallback(self, val, index):
        # Used for epics callbacks
        if val.ok == False:
            self.status[index] = self.ERROR
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
        else:

            enum = val.enums
            newstate = enum[val]
        
            if newstate == "ON":
                self.statusfbk[index] = self.ON
            elif newstate == "OFF":
                self.statusfbk[index] = self.OFF
            else:
                self.statusfbk[index] = self.ERROR            
        
        self.emitCallback(unit = index)
            
    def updateStatusCallback(self, val, index):
        if val.ok == False:
            self.status[index] = self.ERROR
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
        else:
            cmd = val.enums[val]
            logging.debug("Status = %s (%s)", cmd, val.name)
            if cmd == "ON":
                self.status[index] = self.ON
                self.statusText[index] = ""
            elif cmd == "OFF":
                self.status[index] = self.OFF
                self.statusText[index] = ""
            elif cmd == "NO CONNECTION":
                self.status[index] = self.FAULT
                self.statusText[index] = "No Conn."
            elif cmd == "ACCELERATING":
                self.status[index] = self.ACCEL
                self.statusText[index] = "Accel."
            elif cmd == "BRAKE":
                self.status[index] = self.BRAKE
                self.statusText[index] = "Brake" 
            elif cmd == "FAULT":
                self.status[index] = self.FAULT
                self.statusText[index] = "Fault" 
            else:
                self.status[index] = self.FAULT
                self.statusText[index] = val
        self.emitCallback(unit = index)
        return

    def getStatus(self, unit):
        if (self.status[unit] == self.ON) and (self.statusfbk[unit] == self.OFF):
            return self.FAULT
        if (self.status[unit] == self.OFF) and (self.statusfbk[unit] == self.ON):
            return self.FAULT
        else:
            return self.status[unit]

    def getValue(self, unit):
        if self.status[unit] == self.ON:
            return 1
        else:
            return 0

    def getStatusMessage(self, unit):
        return self.statusText[unit]
    

class EpicsAreaDetectorImage(EpicsBase):
    def __init__(self, pvName = [None]):
        EpicsBase.__init__(self)

        self.dimsaddr = [i + ":Dimensions_RBV" for i in pvName]
        self.imageaddr = [i + ":ArrayData" for i in pvName]
       
        self.status = [self.ERROR for i in pvName]
        self.statusText = ["Error" for i in pvName]
        
        self.arraySize = [None for i in pvName]
        self.value = [None for i in pvName]

        self.initialized = False

    def init(self):
        # Setup callbacks for EPICS PVs
        self.addEpicsCallback(self.dimsaddr, self.updateCallback)
        self.addEpicsCallback(self.imageaddr, self.updateImageCallback)
        self.initialized = True
        return True

    def getInformation(self, unit):
        newunit = unit
        text = ""
        text += "PV : %s" % self.imageaddr[newunit]
        text += "\n"
        text += "Status = %s\n" % self.NICETEXT[self.status[newunit]]
        text += "Status Text = %s\n" % self.statusText[newunit]
        return "EPICS AreaDetector Image", text

    def updateCallback(self, val, index):
        # Used for epics callbacks
        if val.ok == False:
            self.status[index] = self.ERROR
            self.imagedata = None
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
        else:
            self.arraySize = val[0:3]
        
    def updateImageCallback(self,val,index):
        if val.ok == False:
            self.status[index] = self.ERROR
            logging.warning("Error on EPICS callback for %s error = %s", val.name, str(val))
        else:
            if self.arraySize is not None:
                if self.arraySize[2] == 0:
                    sz = self.arraySize[0:2][::-1]
                    data = numpy.array(val[:sz.prod()],dtype = numpy.uint16)
                    data = data.reshape(sz)
                else:
                    sz = self.arraySize[0:3][::-1]
                    data = val[:sz.prod()]
                    data = data.reshape(sz)
                self.status[index] = self.ON
                self.value[index] = data
            else:
                self.status[index] = self.ERROR
                self.value[index] = numpy.ones
                
        self.emitCallback(unix = index)

    def getValue(self, unit):
        return self.value[unit]

if __name__ == "__main__":
    e = EpicsAreaDetectorImage(pvName = ['TARDIS:EXP:CCD:image1'])
    e.init()
    print e.getInformation(0)[1]
    cothread.WaitForQuit()
