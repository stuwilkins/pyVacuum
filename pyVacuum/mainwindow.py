#!/usr/bin/python
#
# pyVacuum.py (c) Stuart B. Wilkins 2008
#
# $Id: mainwindow.py 109 2009-10-19 00:12:25Z swilkins $
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

# Import Standard Libraries

import os
import sys
import math
import numpy
import time
import subprocess
import pickle

# QT
from PyQt4 import QtCore, QtGui, QtSvg
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Config info

import config

# Logfile

import logging as log
logging = log.getLogger(__name__)

from iomodules.objects import * 
import ringbuffer

import ui.aboutbox as aboutbox

from threads import *

import pyVacuum

class pyVacuumAboutDialog(QtGui.QDialog):
    def __init__(self, *args):
        QtGui.QDialog.__init__(self, *args)
        ui = aboutbox.Ui_Dialog()
        ui.setupUi(self)
        
class pyVacWindow(QtGui.QMainWindow):
    def __init__(self, *args):
        QtGui.QMainWindow.__init__(self, *args)

        print logging
        logging.info("Started main window")

        # Images are in the modules directory
        imagesdir = os.path.join(pyVacuum.__path__[0], 'images')

        # Find directory for all config files.

        self.workingDir = config.workingDir

        # Setup comon files

        self.pickleFile = config.pickleFilename
        self.valueLogFile = config.valueLogFilename
        self.backdropFile = config.backdropFilename
        self.processImage = config.processImageFilename

        # Setup widgets

        #self.qwtplot = pyVacGraphWindow(self)
	self.qwtplot = None

        pyvac = pyVac(self)
        self.setCentralWidget(pyvac)

        # Set the icon

        self.setWindowIcon(QtGui.QIcon(os.path.join(imagesdir,"tardisicon.jpg")))

        # Setup Main Window

        self.resize(config.windowSize[0], 
                    config.windowSize[1])

        self.setWindowTitle(config.windowTitle)
        self.statusBar().showMessage("Ready")
        self.connected = False

        # Setup Actions

        self.aboutAction = QtGui.QAction('About', self)
        self.exitAction = QtGui.QAction(
        QtGui.QIcon(os.path.join(imagesdir,'exit-128.png')), 'Quit', self)
        self.exitAction.setShortcut('Ctrl+Q') 
	self.graphAction = QtGui.QAction( QIcon(os.path.join(imagesdir,'graph-128.png')), 'Graph', self) 
	self.configAction = QtGui.QAction( QIcon(os.path.join(imagesdir,'config-128.png')), 'Config', self) 
	self.connectAction = QtGui.QAction( QIcon(os.path.join(imagesdir,'connect-128.png')), 'Connect', self) 
	self.disconnectAction = QtGui.QAction( QIcon(os.path.join(imagesdir,'stop-128.png')), 'Disconnect', self) 
	self.logAction = QtGui.QAction( QIcon(os.path.join(imagesdir,'log-128.png')), 'Log', self)
        self.dataAction = QtGui.QAction( QIcon(os.path.join(imagesdir,'filesaveas-128.png')), 'Log', self)

        self.connect(self.aboutAction, QtCore.SIGNAL('triggered()'), 
                     self.showAbout)
        self.connect(self.exitAction, QtCore.SIGNAL('triggered()'), 
                     self, QtCore.SLOT('close()'))
        #self.connect(self.graphAction, QtCore.SIGNAL('triggered()'), 
        #             self.qwtplot, QtCore.SLOT('show()'))
        #self.connect(self.graphAction, QtCore.SIGNAL('triggered()'), 
        #             self.qwtplot, QtCore.SLOT('raise()'))
        self.connect(self.connectAction, QtCore.SIGNAL('triggered()'), 
                     self.connectAll)
        self.connect(self.disconnectAction, QtCore.SIGNAL('triggered()'), 
                     self.disconnectAll)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        configMenu = menubar.addMenu('&Config')
        windowMenu = menubar.addMenu('&Window')

        fileMenu.addAction(self.connectAction)
        fileMenu.addAction(self.disconnectAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.aboutAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAction)

        configMenu.addAction(self.configAction)
        windowMenu.addAction(self.graphAction)
        
        self.toolBar = self.addToolBar('Main')
        self.toolBar.addAction(self.exitAction)
        self.toolBar.addAction(self.configAction)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.graphAction)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.connectAction)
        self.toolBar.addAction(self.disconnectAction)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.logAction)
        self.toolBar.addAction(self.dataAction)

        self.flashTimer = QtCore.QTimer(self)
        self.flashTimer.setInterval(1000)
        self.connect(self.flashTimer, QtCore.SIGNAL('timeout()'),
                     self.flashIcon)
        self.flashIcon = [QIcon(os.path.join(imagesdir,"connect-flash-128.png")),
                          QIcon(os.path.join(imagesdir,"connect-128.png"))]
        self.flash = 0

        self.connectAll()

    def showAbout(self):
        d = pyVacuumAboutDialog()
        d.exec_()

    def graphWindow(self):
        return self.qwtplot

    def flashIcon(self):
        self.flash = self.flash ^ 1
        self.connectAction.setIcon(self.flashIcon[self.flash])

    def connectAll(self):
        if self.connected == False:
            if self.centralWidget().connectAll() == True:
                self.flashTimer.start()
                self.connected = True

    def disconnectAll(self):
        if self.connected == True:
            self.centralWidget().disconnectAll()
            self.flashTimer.stop()
            self.connected = False
            self.connectAction.setIcon(self.flashIcon[1])


    def closeEvent(self, ev):
        self.centralWidget().pickleRingbuffers(self.pickleFile)
        for t in  self.centralWidget().thread:
            t.stop()
        ev.accept()
    

class pyVac(QtGui.QWidget):
    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)

        # Setup backdrop

        if  self.parentWidget().backdropFile is not None:
            self.diagram = QtGui.QImage(self.size(), 
                                        QtGui.QImage.Format_RGB16)

            backdrop = self.parentWidget().backdropFile
            logging.info("pyVac() : Loading backdrop %s" % backdrop)
            self.diagram.load(backdrop)
        else:
            self.diagram = None

        # setup logger

        self.lastLogWrite = 0
        
        logging.info("pyVacuum started")

        # Configure Interval Timer

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(config.timerInterval)
        self.connect(self.timer, QtCore.SIGNAL('timeout()'),
                     self.updateAll)

        self.timer2 = QtCore.QTimer(self)
        self.timer2.setInterval(5000)
        self.connect(self.timer2, QtCore.SIGNAL('timeout()'),
                     self.dumpWidget)
        #self.connect(self.timer2, QtCore.SIGNAL('timeout()'),
        #             self.parentWidget().graphWindow().getPlot().dumpWidget)

        # Load the controllers from the config file
        self.controllers = config.controllers

        # Setup the objects but use no controller when
        # we connect we will call __init__ again!

        self.objects = []
        self.objectinfo = config.guiobjects
        for object in self.objectinfo:
            # Make a copy and set the controller to None
            kwargs = object[1].copy()
            kwargs['controller'] = None
            self.objects.append(object[0](self, **kwargs)) 

        # Get picked ringbuffers

        self.getPickledRingbuffers(self.parentWidget().pickleFile)

        # Setup thread to update the controllers
        self.thread = []
        for c in self.controllers:
            if c is not None:
                if c.needsPolling:
                    self.thread.append(pyVacThread(controller = c))
                    self.thread[-1].start()
        
        # Setup the value logger

        self.setupValueLog(self.parentWidget().valueLogFile)

        # Start interval timer

        self.timer.start()
        self.timer2.start()
        logging.info("Timer started")

    def disconnectAll(self):
        """
        Disconnect all controllers and stop the thread
        """
        for t in self.thread:
            t.setNoUpdate(True)
            logging.info("Stopped controllers thread")

        for c in self.controllers:
            c.close()
            logging.info("Closing controller %s" % str(c))

        for o in self.objects:
            o.setController(None)
            o.setDefaultActions()
            logging.info("Disconnecting object %s" % str(o))

    def initAll(self):
        flag = False
        for x in range(len(self.controllers)):
            logging.info("Trying to initialize controller %d" % x)
            if self.controllers[x] is not None:
                if self.controllers[x].init():
                    logging.info("Controller %d initialized" % x)
                else:
                    logging.warning("Controller %d (%s) failed to initialize" % 
                                    (x,str(self.controllers[x])))
        return True

    def connectAll(self):
        """
        Connect to all controllers and start the thread 
        """
        # Configure Controllers and Objects
        # Stop if we cannot configure 

        self.initAll()

        # Now see what items can be turned on!

        for o in range(len(self.objectinfo)):
            controller = self.objectinfo[o][1]['controller']
            if controller is not None:
                u = self.objectinfo[o][1]['unit']
                flag = True
                if type(controller) is not type([]):
                    if not controller.isInitialized(u):
                        flag = False
                else:
                    for c in range(len(controller)):
                        if controller[c].isInitialized(u[c]) == False:
                            flag = False
                            break
                
                if flag == True:
                    # All controllers are init
                    self.objects[o].setController(controller)
                    logging.info("Controller on object %d Initialized OK" % o)
                    # Add the actions to the devices
                    self.objects[o].setActions()
                else:
                    logging.warning("Failed to initialize controller on object %d (%s)" % (o , self.objects[o].getName()))

        logging.info("%d controllers configured" % len(self.controllers))
        logging.info("%d object configured" % len(self.objects))
        for t in self.thread:
            t.setNoUpdate(False)
        logging.info("Started controllers thread")
        return True
    
    def setupValueLog(self, filename):
        s = ""
        for o in self.objects:
            if o.isLoggable():
                s = s + config.valueLogSep
                s = s + config.valueLogStringFormat % o.getName()
        
        if s != "":
            if filename is not None:
                f = open(filename, 'a')
                f.write('#\n# Logfile started at %s (%f)\n#\n' % 
                        (time.asctime(), time.time()))
                f.write('# TIME%s\n' % s)
                f.close()

    def writeValueLog(self, filename):
        s = ""
        for o in self.objects:
            if o.isLoggable() == True:
                v = o.getValue()
                try:
                    nval = float(v)
                    s = s + config.valueLogSep + config.valueLogFormat % nval
                except:
                    s = s + config.valueLogSep + config.valueLogStringFormat % v
            
        if s != "":
            if filename is not None:
                f = open(filename, 'a')
                f.write('%f%s\n' % (time.time(), s))
                f.close()

    def dumpWidget(self):

        if self.parentWidget() is not None:
            pixmap = QtGui.QPixmap.grabWidget(self.parentWidget())
        else:
            pixmap = QtGui.QPixmap.grabWidget(self)
            
        pixmap.save(self.parentWidget().processImage)
        
    def updateAll(self):

        # Update all objects by calling update()
        r = []
        for n in self.objects:
            r.append(n.updateFromController())
            n.updateRingBuffer()

        # Write a line in the log file
        
        if (time.time() - self.lastLogWrite) > config.logInterval:
            self.writeValueLog(self.parentWidget().valueLogFile)
            self.lastLogWrite = time.time()

        # Now update graph
	"""
        if self.parentWidget() is not None:
            plot = self.parentWidget().graphWindow().getPlot()
            for x in self.objects:
                if x.getRingBuffer().nValues() > 1:
                    data = x.getRingBuffer().get()
                    dx = data[:,0]
                    dy = data[:,1]
                    plot.plotData(x.getName(), x.toYPlot(), dx, dy)
            self.parentWidget().statusBar().showMessage("Last updated %s" % 
                                                        time.asctime(time.localtime()))
            plot.replot()
	"""

    def pickleRingbuffers(self, filename):
        try:
            f = open(filename, 'w')
        except:
            logging.critical("pickleRingbuffers() : Unable to write to %s" % filename)
        
        for o in self.objects:
            pickle.dump(o.getName(), f)
            pickle.dump(o.getRingBuffer(), f)
            logging.info("pickleRingbuffers() : Pickled ringbuffer %s" % 
                         o.getName())
        f.close()

    def getPickledRingbuffers(self, filename):
        try:
            f = open(filename, 'r')
            logging.info("getPickledRingbuffers() : Opened %s for ringbuffer pickle." % filename)
        except:
            return False

        for o in self.objects:
            try:
                n = pickle.load(f) 
            except:
                logging.critical("getPickledRingbuffers() : Could not unpickle object name") 
                f.close()
                return False

            if n == o.getName():
                try:
                    rb = pickle.load(f)
                except:
                    f.close()
                    logging.critical("getPickledRingbuffers() : Could not unpickle ringbuffer") 
                    return False
                

                logging.info("getPickledRingbuffers() : Loading pickled ringbuffer for %s" % o.getName())
                o.setRingBuffer(rb)
                
        f.close()
        return True

    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        if self.diagram is not None:
            p.drawImage(0, 0, self.diagram)

    
#
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/mainwindow.py $
#
