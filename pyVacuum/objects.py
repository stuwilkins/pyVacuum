#
# objects.py (c) Stuart B. Wilkins 2008
#
# $Id: objects.py 122 2009-10-26 10:50:50Z swilkins $
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/objects.py $
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
import math
import numpy
import time

from PyQt4 import Qt, QtCore, QtGui

from iomodules.objects import *
import ringbuffer

from plots import CCDTwoDPlot

from log import setupLog
logging = setupLog(__name__)

class pyVacObject(QtGui.QWidget):

    statusc = { VacObject.ERROR : QtGui.QColor(QtCore.Qt.lightGray),
                VacObject.ON    : QtGui.QColor(QtCore.Qt.darkGreen),
                VacObject.OFF   : QtGui.QColor(QtCore.Qt.red),
                VacObject.ACCEL : QtGui.QColor(QtCore.Qt.green),
                VacObject.BRAKE : QtGui.QColor(QtCore.Qt.darkRed),
                VacObject.FAULT : QtGui.QColor(QtCore.Qt.yellow),
                VacObject.DEGAS : QtGui.QColor(QtCore.Qt.green),
                VacObject.OPEN  : QtGui.QColor(QtCore.Qt.darkGreen),
                VacObject.CLOSE : QtGui.QColor(QtCore.Qt.red)}
    

    statusText = { VacObject.ERROR : "ERROR",
                   VacObject.ON    : "ON",
                   VacObject.OFF   : "OFF",
                   VacObject.ACCEL : "ACCEL",
                   VacObject.BRAKE : "BRAKE",
                   VacObject.FAULT : "FAULT",
                   VacObject.DEGAS : "DEGAS",
                   VacObject.OPEN  : "OPEN",
                   VacObject.CLOSE : "CLOSE"}
        
    
    def __init__(self, parent = None, 
                 name = "", 
                 controller = None, 
                 unit = None,
                 x = 0, y = 0, 
                 controlable = True,
                 plotable = True,
                 loggable = True,
                 format = "%f",
                 bufferlen = 20000,
                 callback = None,
                 **kwargs):

        QtGui.QWidget.__init__(self, parent)

        # Store passed variables

        self.controlable = controlable
        self.plotable = plotable
        self.loggable = loggable
        self.format = format
        self.emitCallback = callback

        if type(controller) == type([]):
            self.controller = controller
        else:
            self.controller = [ controller ]

        if type(unit) == type([]):
            self.unit = unit
        else:
            self.unit = [ unit ]

        self.name = name
        self.status = VacObject.ERROR
        self.statusMessage = ""
        self.value = 0
        self.valueUnits = "None"
        self.yplot = 0

        # Locate object

        self.move(x, y)

        # Setup ringbuffer

        self.ringbuffer = ringbuffer.RingBuffer(bufferlen)
        self.ringBufferUpdate = 10
        self.lastRingBufferUpdate = 0

        # Time of update
        
        self.lastUpdate = time.localtime()

        # Setup menu of actions for this control
        self.popup = QtGui.QMenu(self.name, self)
        self.popup.setTearOffEnabled(True)
        QtCore.QObject.connect(self.popup, 
                               QtCore.SIGNAL('triggered(QAction *)'),
                               self.actionTriggered)
        self.setDefaultActions()

        # Setup standard labels

        self.nameLabel = QtGui.QLabel(self)
        self.nameLabel.hide()
        self.nameLabel.setText(self.name)

        self.statusLabel = QtGui.QLabel(self)
        self.statusLabel.hide()

        self.valuebox = QtGui.QLabel(self)
        self.valuebox.hide()

        self.noUpdate = False

    def setDefaultActions(self):
        """This routine clears the popup of all actions and re-initializes"""
        self.popup.clear()
        action = QtGui.QAction(self.name, self.popup)
        action.setEnabled(False)
        self.popup.addAction(action)
        self.popup.addSeparator()

    def setActions(self):
        """Reads the actions from the controller and adds them to the popup menu"""
        if self.controller != [None]:
            if self.controlable:
                actions = self.controller[0].getActions(self.unit[0])
                for action in actions.keys():
                    self.popup.addAction(action)
                self.popup.addSeparator()
                i = self.popup.addAction("Info")
                i.setCheckable(False)
                self.popup.addSeparator()
            return True
        return False

    def getController(self):
        return self.controller

    def setController(self, c):
        if type(c) is not type([]):
            self.controller = [c]
        else:
            self.controller = c

    def setCallbacksToControllers(self):
        """Link our callback routine to controller"""
        flag = True
        for c in self.controller:
            if not c.addCallback(self.controllerCalledback):
                logging.error("setCallbackToController() : Unable to set callback")
                flag = False
        return flag

    def controllerCalledback(self, controller, *args, **kwargs):
        """The controller calledback, so update!"""
        if controller in self.controller:
            self.updateFromController()
        else:
            logging.error("controllerCalledback() : BAD CALLBACK")

    def updateFromController(self, controller = None, unit = None):
        """
        Read the controller and get the value, status and units
        returns True if sucsesful, False if there was an error
        """
        
        logging.debug("updateFromController() : Updating %s", self.name)

        if self.noUpdate == True:
            return False
        
        flag = False
        for c,u in zip(self.controller, self.unit):
            if c is not None:
                self.status = c.getStatus(u)
                if self.status != VacObject.ERROR:
                    self.statusMessage = c.getStatusMessage(u)
                    if (self.status != VacObject.OFF):
                        self.valueUnits = c.getUnits(u)
                        self.value = c.getValue(u)
                        flag = True
                        break
                    else:
                        self.valuebox.setText("")
                else:
                    self.statusMessage = ""
            else:
                logging.debug("updateFromController() : %s has no controller", self.name)
              
        self.lastUpdate = time.localtime()
        self.updateValueLabel()
        self.updateStatusLabel()
        self.updateRingBuffer()
        self.updateDisplay()
        if self.emitCallback is not None:
            self.emitCallback()
        self.update()
        return flag

    def updateValueLabel(self):
        self.valuebox.setText((self.format + " %s") %
                              (self.value, self.valueUnits))

    def updateStatusLabel(self):
        self.statusLabel.setText(self.statusMessage)

    def updateDisplay(self):
        return

    def getName(self):
        return self.name

    def updateRingBuffer(self):
        if (self.status != VacObject.OFF) and (self.status != VacObject.ERROR):
            self.ringbuffer.append([time.time(), self.value])

    def getNameLabel(self):
        return nameLabel

    def getStatusLabel(self):
        return statusLabel

    def getValueLabel(self):
        return valuebox

    def actionTriggered(self, ev):

        t = ev.text()

        if t == "Info":
            self.showControllerInformation()
            return

        if self.controller[0] == None:
            # Ignore this action
            return

        a = self.controller[0].getActions(self.unit[0])

        # Now check status change for object
        newstatus = -1
        for d in a.keys():
            if d == t:
                newstatus = a[d]
                logging.info("Status changed to %s (%d)" % (t, newstatus))
                self.controller[0].setStatus(self.unit[0], newstatus)
                break
        if newstatus == -1:
            logging.warning("Unknown action %s" % t)

        return 
    
    def getRingBuffer(self):
        return self.ringbuffer

    def setRingBuffer(self, rb):
        self.ringbuffer = rb

    def setNameLabel(self, x, y, align = QtCore.Qt.AlignCenter,
                     width = 90, height = 20, fontsize = 12):
        self.nameLabel.move(x, y)
        self.nameLabel.resize(width, height)
        self.nameLabel.setAlignment(align)
        self.nameLabel.setFont(QtGui.QFont("helvetica", fontsize, 
                                           QtGui.QFont.Bold))
        self.nameLabel.show()

    def setValueLabel(self, x, y, align = QtCore.Qt.AlignLeft,
                      width = 90, height = 20, fontsize = 10):
        self.valuebox.move(x, y)
        self.valuebox.resize(width, height)
        self.valuebox.setAlignment(align)
        self.valuebox.setFont(QtGui.QFont("helvetica", fontsize, 
                                          QtGui.QFont.Bold))
        self.valuebox.show()

    def setStatusLabel(self, x, y, align = QtCore.Qt.AlignLeft,
                       width = 90, height = 20, fontsize = 10,
                       frame = False):
        self.statusLabel.move(x, y)
        self.statusLabel.resize(width, height)
        self.statusLabel.setAlignment(align)
        self.statusLabel.setFont(QtGui.QFont("helvetica", fontsize, 
                                          QtGui.QFont.Bold))
        if frame:
            self.statusLabel.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
            
        self.statusLabel.show()

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.popup.popup(self.mapToGlobal(ev.pos()))

    def showControllerInformation(self):
        a , b = self.controller[0].getInformation(self.unit[0])
        msgBox = QtGui.QMessageBox()
        msgBox.setIcon(QtGui.QMessageBox.Information)
        msgBox.setText(a)
        msgBox.setWindowTitle(self.name)
        msgBox.setInformativeText(b)
        msgBox.setStandardButtons(QtGui.QMessageBox.Cancel)
        msgBox.setWindowModality(QtCore.Qt.WindowModal)
        msgBox.exec_()
        self.msgBoxRtn = msgBox

    def mouseDoubleClickEvent(self, ev):
        if self.controller[0] is not None:
            type = self.controller[0].isSettable(self.unit[0])
            if type:
                self.inputBox = QtGui.QInputDialog(self)
                self.inputBox.setInputMode(QtGui.QInputDialog.TextInput)
                self.inputBox.setWindowTitle(self.name)
                self.inputBox.setLabelText("")
                QtCore.QObject.connect(self.inputBox, 
                                       QtCore.SIGNAL('accepted()'),
                                       self.inputBoxTriggered)
                self.inputBox.exec_()
                
    def inputBoxTriggered(self):
        val = self.inputBox.textValue()
        self.controller[0].setValue(self.unit[0], str(val))
        
    def getValue(self):
        return self.value

    def isLoggable(self):
        return self.loggable

    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.HighQualityAntialiasing, True)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        self.paintObject(p)
        p.end()

    def paintObject(self, p):
        return
 
class pyVacPump(pyVacObject):
    
    ION = 0
    TURBO = 1
    ROUGH = 2
    TSP = 3

    LEFT = 1;
    RIGHT = 2;
    TOP = 4;
    BOTTOM = 16;

    def __init__(self, parent = None, 
                 port = LEFT, type = None,
                 **kwargs):
        kwargs['format'] = "%3.2e"
        pyVacObject.__init__(self, parent, **kwargs)
        
        self.type = type
        self.port = port
        self.resize(90, 150)
        self.move(kwargs['x'] - 45, kwargs['y'] - 45)
        self.setNameLabel(0, 90, QtCore.Qt.AlignCenter)
        if (type == self.ION):
            self.setValueLabel(0, 130, QtCore.Qt.AlignCenter)
        if (type == self.TURBO) or (type == self.ION):
            self.setStatusLabel(0, 110, QtCore.Qt.AlignCenter)

    def paintObject(self, p):
        
        p.setBrush(QtGui.QColor("Black"))
        if self.port & self.LEFT:
            p.drawRect(0, 43, 10, 5)
        if self.port & self.RIGHT:
            p.drawRect(80, 43, 10, 5)
        if self.port & self.TOP:
            p.drawRect(43, 0, 5, 10)

        p.setBrush(self.statusc[self.status])

        r = 35
        
        p.setPen(QtGui.QPen(QtGui.QColor("Black"), 2))
        p.drawEllipse(10, 10, r * 2, r * 2)
        a = (10 + r) + (r * math.sin(10 * math.pi / 180))
        b = (10 + r) + (r * math.cos(10 * math.pi / 180))
        c = (10 + r) + (r * math.sin(100 * math.pi / 180))
        d = (10 + r) + (r * math.cos(100 * math.pi / 180))
        p.drawLine(a , b, c, d)
        a = (10 + r) + (r * math.sin(-10 * math.pi / 180))
        b = (10 + r) + (r * math.cos(-10 * math.pi / 180))
        c = (10 + r) + (r * math.sin(-100 * math.pi / 180))
        d = (10 + r) + (r * math.cos(-100 * math.pi / 180))
        p.drawLine(a , b, c, d)

        if self.type == self.ION:
            # Ion pump
            # Three arrows from center
            arrow = QtGui.QPolygon(3)
            line = QtCore.QLine(0, 0, 0, 20)
            matrix = QtGui.QMatrix()
            arrow.setPoints(-5, -5, 
                             5, -5, 
                             0, 5)
            arrow.translate(0, 20)
            
            for i in range(3):
                matrix.rotate(120)
                a = matrix.map(arrow)
                b = matrix.map(line)
                a.translate(10 + r, 10 + r)
                b.translate(10 + r, 10 + r)
                p.setPen(QtGui.QPen(QtGui.QColor("Black"), 1))
                p.setBrush(QtGui.QColor("Black"))
                p.drawPolygon(a)
                p.setPen(QtGui.QPen(QtGui.QColor("Black"), 2))
                p.drawLine(b)
            
        elif self.type == self.TURBO:
            p.drawEllipse(10 + r/2, 10 + r/2, r , r )
            p.drawEllipse(10 + (r * 3 / 4), 10 + (r * 3 / 4), r / 2 , r / 2)

        elif self.type == self.ROUGH:
            p.drawEllipse(10 + r/2, 10 + r/2, r , r )
            b = QtGui.QPolygon(3)
            b.setPoints(0, 0, 6, 6, 0, 12)
            b.translate(7 + r, 5 + r/2)
            p.setBrush(QtGui.QColor("Black"))
            p.drawPolygon(b)
        
class pyVacGauge(pyVacObject):
    def __init__(self, parent = None, **kwargs):
        if not kwargs.has_key('format'):
            kwargs['format'] = "%3.2e"
        pyVacObject.__init__(self, parent, **kwargs)
        self.resize(150, 60)
        self.move(kwargs['x'] , kwargs['y'] - 60)
        self.setValueLabel(45,0, QtCore.Qt.AlignLeft)
        self.setNameLabel(45, 20, QtCore.Qt.AlignLeft)
        self.setStatusLabel(45, 40, QtCore.Qt.AlignLeft)
        
    def paintObject(self, p):
        p.setBrush(QtGui.QColor("Black"))
        p.drawRect(18, 40, 5, 20)
        p.setBrush(self.statusc[self.status])
        p.drawEllipse(0, 15, 40, 40)
        p.setPen(QtGui.QPen(QtGui.QColor("Black"), 2))
        p.drawLine(5,30,35,30)
        p.drawLine(20,45,10,25)
        p.drawLine(20,45,30,25)
        
class pyVacValve(pyVacObject):
    AUTOMATIC = 0
    MANUAL = 1

    def __init__(self, parent = None, type = AUTOMATIC, **kwargs):
        pyVacObject.__init__(self, parent, format = "%d", **kwargs)

        self.type = type
        self.resize(100,100)
        self.move(kwargs['x'] - 50, kwargs['y'] - 50)
        self.setNameLabel(5, 80, QtCore.Qt.AlignCenter)

    def paintObject(self, p):
        a = QtGui.QPolygon(3)
        b = QtGui.QPolygon(3)
        
        a.setPoints(10, 30, 10, 70, 50, 50)
        b.setPoints(50, 50, 90, 30, 90, 70)
        
        p.setBrush(self.statusc[self.status])
        p.drawPolygon(a)
        p.drawPolygon(b)
        p.setBrush(QtGui.QColor("Black"))
        p.drawRect(0, 48, 10, 5)
        p.drawRect(90, 48, 10, 5)
        p.drawRect(48, 30, 5, 20)
        if self.type == self.AUTOMATIC:
            p.setBrush(QtGui.QColor("DarkRed"))
            p.drawRect(45, 10, 10, 20)
        elif self.type == self.MANUAL:
            p.drawRect(48, 10, 5, 20)
            p.drawRect(40, 10, 20, 5)
        
class pyVacSensor(pyVacObject):
    THERMO = 1
    def __init__(self, parent = None, type = THERMO, **kwargs):
        pyVacObject.__init__(self, parent, **kwargs)
        self.resize(90,100)
        self.move(kwargs['x'] - 45, kwargs['y'] - 50)
        self.setNameLabel(0, 80, QtCore.Qt.AlignCenter)
        self.setValueLabel(0, 60,  QtCore.Qt.AlignCenter)
        self.value = 0.0
        self.type = type

    def paintObject(self, p):
        pen = QtGui.QPen(self.statusc[self.status], 2)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        p.setPen(pen)
        p.drawLine(10, 20, 40, 20)
        p.drawLine(10, 40, 40, 40)
        p.drawLine(40, 20, 60, 30)
        p.drawLine(40, 40, 60, 30)
        p.setBrush(self.statusc[self.status])
        p.drawEllipse(55, 25, 10, 10)
        
class pyVacChamber(pyVacObject):
    PUMPED = 1
    NOTPUMPED = 2
    def __init__(self, parent, **kwargs):
        kwargs['format'] = "%3.2e"
        pyVacObject.__init__(self, parent, controlable = False, **kwargs)
        width = kwargs['width']
        height = kwargs['height']
        self.resize(width,height)
        self.move(kwargs['x'], kwargs['y'])
        self.border = 10
        self.setNameLabel(self.border * 2, height - 100, 
                          QtCore.Qt.AlignCenter,
                          width = width - (self.border * 4))
        self.setValueLabel(self.border * 2, height - 150, 
                           QtCore.Qt.AlignCenter,
                           width = width - (self.border * 4),
                           height = 40, fontsize = 18)
        
        self.status = VacObject.ERROR
    
    def paintObject(self, p):
        pen = QtGui.QPen(self.statusc[self.status], 5)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(QtGui.QBrush(QtGui.QColor("LightGrey")))
        p.drawRect(self.border, self.border, 
                   self.size().width() - (self.border * 2), 
                   self.size().height() - (self.border * 2))

"""
Removed due to QWT


class pyVacRGA(pyVacObject):
     def __init__(self, parent, **kwargs):
         kwargs['format'] = '%5.2f'
         pyVacObject.__init__(self, parent, **kwargs)

         self.resize(kwargs['width'], kwargs['height'])
         self.move(kwargs['x'], kwargs['y'])
         
         self.setNameLabel(0, kwargs['height'] - 50, QtCore.Qt.AlignCenter)
         self.setValueLabel(150, kwargs['height'] - 50, QtCore.Qt.AlignCenter)
         self.setStatusLabel(300, kwargs['height']- 50, QtCore.Qt.AlignCenter)

         self.graphWindow = Qwt.QwtPlot(self)
         self.graphWindow.move(0,0)
         self.graphWindow.resize(kwargs['width'], kwargs['height']- 50)

         self.rgaData = pyVacRGACurve("RGA Data")
         self.rgaData.setColor(QtGui.QColor('Red'))
         self.rgaData.setYAxis(Qwt.QwtPlot.yLeft)
        
         self.rgaWipe = Qwt.QwtPlotCurve("Wipe")
         self.rgaWipe.setYAxis(Qwt.QwtPlot.yLeft)

         self.graphWindow.setAxisScaleEngine(Qwt.QwtPlot.yLeft, 
                                             Qwt.QwtLinearScaleEngine())
         self.graphWindow.setAxisScaleDraw(Qwt.QwtPlot.yLeft,
                                           pyVacRGAScaleDraw())
         self.graphWindow.setAxisTitle(Qwt.QwtPlot.xBottom,
                                       "Mass Number [m/Z]")
         self.graphWindow.setAxisTitle(Qwt.QwtPlot.yLeft,
                                       "Pressure [torr]")
         
         self.rgaData.attach(self.graphWindow)
         self.rgaWipe.attach(self.graphWindow)
         self.graphWindow.show()

     def updateDisplay(self):
         if self.controller[0] is not None:
             x = self.controller[0].getMassRange()
             self.graphWindow.setAxisScale(Qwt.QwtPlot.xBottom, x[0], x[1])
             
             bgnd = self.controller[0].getZeroData()
             data = self.controller[0].getData()
             if data.shape != (0,):
                 data[(data[:,1] < bgnd[1]), 1] = bgnd[1]
                 self.rgaData.setData(data[:,0], log10(data[:,1] / bgnd[1]))
             
                 cmass = self.controller[0].getCurrentMass()
                 print cmass 
                 if cmass:
                     x = array([cmass, cmass])
                     y = array([1, log10(max(data[:,1]) / bgnd[1])]) 
                     self.rgaWipe.setData(x, y)
                 self.graphWindow.replot()
                 self.graphWindow.update()

     def paintObject(self, p):
         return

class pyVacRGAScaleDraw(Qwt.QwtScaleDraw):
    def __init__(self):
        Qwt.QwtScaleDraw.__init__(self)
    def label(self, v):
        s = "%e" % pow(v, 10)
        s = QtCore.QString(s)
        return Qwt.QwtText(s)

    def font(self, f, _):
        result = QFont(f)
        result.setPointSize(int(f.pointSize()*1.25))
        return result

class pyVacRGACurve(Qwt.QwtPlotCurve):
    def __init__(self, *args):
        Qwt.QwtPlotCurve.__init__(self, *args)
        self.setRenderHint(Qwt.QwtPlotItem.RenderAntialiased)
        
    def setColor(self, color):
        color.setAlpha(150)
        self.setPen(color)
        self.setBrush(color)
"""
class pyVacNSLS(pyVacObject):
    def __init__(self, parent, **kwargs):
        kwargs['format'] = '%5.2f'
        pyVacObject.__init__(self, parent, **kwargs)
        self.resize(90,100)
        self.move(kwargs['x'] - 45, kwargs['y'] - 50)

        self.setNameLabel(0, 80, QtCore.Qt.AlignCenter)
        self.setValueLabel(0, 60, QtCore.Qt.AlignCenter)
        
    def paintObject(self, p):
        pen = QtGui.QPen(self.statusc[self.status], 3)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        p.setPen(pen)

        ly = 0
        lx = 0
        for i in range(1,100):
            y = sin( 2 * pi * i * 4 / 100 ) * 10 
            p.drawLine(i - 1, ly + 30, i, y + 30)
            ly = y

        return

class pyVacWebImage(pyVacObject):
    def __init__(self, parent, **kwargs):
        pyVacObject.__init__(self, parent, **kwargs)
        self.resize(kwargs['width'], kwargs['height'])
        self.move(kwargs['x'], kwargs['y'])
        self.image = QtGui.QImage()
        self.active = False

    def paintObject(self, p):
        if self.active:
            imageAspect = float(self.image.size().width()) / float(self.image.size().height())
            widgetAspect = float(self.size().width()) / float(self.size().height())
            if imageAspect < widgetAspect:
                p.drawImage(0, 0, 
                            self.image.scaledToHeight(self.size().height()))
            else:
                p.drawImage(0, 0, 
                            self.image.scaledToWidth(self.size().width()))

    def updateFromController(self):
        if self.controller != [None]:
            i = self.controller[0].getImage()
            if self.image.loadFromData(i):
                self.active = True
                self.update()
            else:
                self.actve = False

class pyVacStatusMessage(pyVacObject):
    def __init__(self, parent, **kwargs):
        pyVacObject.__init__(self, parent, **kwargs)
        self.move(kwargs['x'], kwargs['y'])
        self.resize(kwargs['xsize'], kwargs['ysize'])
        self.active = True
        self.setStatusLabel(0,0, 
                            align = QtCore.Qt.AlignCenter,
                            width = kwargs['xsize'], height = kwargs['ysize'],
                            fontsize = 16, frame = True)
        self.statusLabel.show()

class pyVacLCD(pyVacObject):
    def __init__(self, parent, **kwargs):
        pyVacObject.__init__(self, parent, **kwargs)
        if kwargs.has_key('width'):
            width = kwargs['width']
        else:
            width = 100
        self.resize(width, 80)
        self.move(kwargs['x'] - 50, kwargs['y'] - 40)
        self.active = False
        self.setNameLabel(5, 55, QtCore.Qt.AlignCenter, width = width, fontsize = 11)
        self.lcd = QtGui.QLCDNumber(self) 
        self.lcd.setSegmentStyle(self.lcd.Filled)
        self.lcd.resize(width, 50)
        self.lcd.display("Err")
        self.setColor()
        
    def updateDisplay(self):
        if self.status == VacObject.ON:
            self.lcd.display(self.value)
            self.setColor(QtGui.QColor("DarkGreen"))
        elif self.status == VacObject.FAULT:
            self.lcd.display(self.statusMessage)
            self.setColor(QtGui.QColor("DarkRed"))

    def setColor(self, clr = QtGui.QColor("DarkRed")):
        palette = self.lcd.palette()
        palette.setColor(QtGui.QPalette.Normal,
                         QtGui.QPalette.WindowText, clr);
        palette.setColor(QtGui.QPalette.Normal,
                         QtGui.QPalette.Background, QtGui.QColor("Black"));
        #palette.setColor(QtGui.QPalette.Normal,
        #                 QtGui.QPalette.Light, QtGui.QColor("Yellow"));
        #palette.setColor(QtGui.QPalette.Normal,
        #                 QtGui.QPalette.Dark, QtGui.QColor("darkYellow"));
        self.lcd.setPalette(palette)
            

class pyVacIndicator(pyVacObject):
    def __init__(self, parent, **kwargs):
        pyVacObject.__init__(self, parent, **kwargs)
        if kwargs.has_key('width') and kwargs.has_key('height'):
            self.size = kwargs['width'], kwargs['height']
        else:
            self.size = 100,80
        self.resize(self.size[0], self.size[1])
        self.move(kwargs['x'] - 50, kwargs['y'] - 40)
        self.active = False
        self.setNameLabel(5, 50, QtCore.Qt.AlignCenter, width = self.size[0] - 10)
        if kwargs.has_key('statustext'):
            self.text = kwargs['statustext']
        else:
            self.text = None
    
        self.indicator = QtGui.QLabel(self)
        self.indicator.resize(self.size[0]-10, self.size[1]-30)
        self.indicator.move(5,0)
        self.indicator.setAlignment(QtCore.Qt.AlignCenter)
        self.indicator.setText("UNK")
        self.indicator.setFont(QtGui.QFont("helvetica", 13, 
                                           QtGui.QFont.Bold))
        self.indicator.setAutoFillBackground(True)
        #self.indicator.set
        
    def updateDisplay(self):
        
        pal = self.indicator.palette();
        pal.setColor(self.indicator.backgroundRole(),
                     self.statusc[self.status])
        self.indicator.setPalette(pal)
        
        if self.text is not None:
            self.indicator.setText(self.text[0])
            if len(self.text) <= self.status:
                status = VacObject.ERROR
            else:
                status = self.status
            
            self.indicator.setText(self.text[status])
        else:
            self.indicator.setText(self.statusMessage)
            
class pyVacCCDImage(pyVacObject):
    def __init__(self, parent, **kwargs):
        pyVacObject.__init__(self, parent, **kwargs)
        self.resize(kwargs['width'], kwargs['height'])
        self.move(kwargs['x'], kwargs['y'])
        self.plotWidget = CCDTwoDPlot(self)

        self.updateCheckBox = QtGui.QCheckBox("Live Update", self)
        self.updateCheckBox.move(625,610)
        self.updateCheckBox.setChecked(True)
        self.connect(self.updateCheckBox,QtCore.SIGNAL('stateChanged(int)'),
                     self.updateCheckBoxChanged)
        
        # Plot the slider for ringbuffer

        self.ringbufferLabel = QtGui.QLabel("Ringbuffer", self)
        self.ringbufferLabel.move(0,610)
        self.ringbufferLabel.resize(100,25)

        self.ringbufferValueLabel = QtGui.QLabel("", self)
        self.ringbufferValueLabel.move(525,610)
        self.ringbufferValueLabel.resize(75,25)

        self.ringbufferSelect = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.ringbufferSelect.move(100,610)
        self.ringbufferSelect.resize(400,25)
        self.ringbufferSelect.setMinimum(0)
        self.ringbufferSelect.setMaximum(0)
        self.ringbufferSelect.setValue(0)
        #self.connect(self.ringbufferSelect,QtCore.SIGNAL('valueChanged(int)'),
        #             self.ringbufferChanged)
        self.ringbufferChanged(0)

    def updateCheckBoxChanged(self, val):
        if not val:
            self.noUpdate = True
        else:
            self.noUpdate = False
            
    def ringbufferChanged(self, val):
        rbval = False
        if val == self.ringbufferSelect.maximum():
             self.ringbufferValueLabel.setText('Current')
             self.updateCheckBox.setChecked(True)
             if self.ringbuffer.nValues():
                 rbval = self.ringbuffer.get(-1)
        else:
            self.ringbufferValueLabel.setText("Image %d" % val)
            self.noUpdate = True
            rbval = self.ringbuffer.get(val)
            self.updateCheckBox.setChecked(False)

        if rbval:
            self.plotWidget.setImage(rbval[1])
            self.plotWidget.setTitle('Image %d' % val)
        
        self.plotWidget.update()
        
    def updateDisplay(self):
        if self.status == VacObject.ON:
            if self.ringbufferSelect.maximum() == self.ringbufferSelect.value():
                # We are updating
                self.plotWidget.setImage(self.value)
                self.plotWidget.setTitle(time.asctime(self.lastUpdate))
                try:
                    self.plotWidget.update()
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                #print self.ringbuffer.nValues()
                self.ringbufferSelect.setMaximum(self.ringbuffer.nValues())
                self.ringbufferSelect.setValue(self.ringbuffer.nValues())
            else:
                # We are on the ringbuffer
                self.ringbufferSelect.setMaximum(self.ringbuffer.nValues())

    def updateValueLabel(self):
        """Fake this"""
        return

