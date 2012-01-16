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

from log import setupLog
logging = setupLog(__name__)

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

        logging.info("Started main window")

        # Images are in the modules directory
        imagesdir = os.path.join(pyVacuum.__path__[0], 'images')

        # Find directory for all config files.

        self.workingDir = config.workingDir

        # Setup comon files

        self.backdropFile = config.backdropFilename

        # Setup widgets

        pyvac = pyVac(self)
        self.setCentralWidget(pyvac)

        # Set the icon

        self.setWindowIcon(QtGui.QIcon(os.path.join(imagesdir,"tardisicon.jpg")))

        # Setup Main Window

        self.resize(config.windowSize[0], 
                    config.windowSize[1])

        self.setWindowTitle(config.windowTitle)
        self.statusBar().showMessage("Initializing")
        self.connected = False

        # Setup Actions

        self.aboutAction = QtGui.QAction('About', self)
        self.exitAction = QtGui.QAction(QtGui.QIcon(os.path.join(imagesdir,'exit-128.png')), 'Quit', self)
        self.exitAction.setShortcut('Ctrl+Q') 
	
	self.configAction = QtGui.QAction( QIcon(os.path.join(imagesdir,'config-128.png')), 'Config', self) 
	self.connectAction = QtGui.QAction( QIcon(os.path.join(imagesdir,'connect-128.png')), 'Connect', self) 
	self.disconnectAction = QtGui.QAction( QIcon(os.path.join(imagesdir,'stop-128.png')), 'Disconnect', self) 
	
        self.connect(self.aboutAction, QtCore.SIGNAL('triggered()'), 
                     self.showAbout)
        self.connect(self.exitAction, QtCore.SIGNAL('triggered()'), 
                     self, QtCore.SLOT('close()'))
        self.connect(self.connectAction, QtCore.SIGNAL('triggered()'), 
                     self.connectAll)
        self.connect(self.disconnectAction, QtCore.SIGNAL('triggered()'), 
                     self.disconnectAll)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        configMenu = menubar.addMenu('&Config')

        fileMenu.addAction(self.connectAction)
        fileMenu.addAction(self.disconnectAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.aboutAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAction)

        configMenu.addAction(self.configAction)
        
        self.toolBar = self.addToolBar('Main')
        self.toolBar.addAction(self.exitAction)
        self.toolBar.addAction(self.configAction)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.connectAction)
        self.toolBar.addAction(self.disconnectAction)

        self.flashTimer = QtCore.QTimer(self)
        self.flashTimer.setInterval(500)
        self.connect(self.flashTimer, QtCore.SIGNAL('timeout()'),
                     self.flashIcon)
        self.flashIcon = [QIcon(os.path.join(imagesdir,"connect-flash-128.png")),
                          QIcon(os.path.join(imagesdir,"connect-128.png"))]
        self.flash = 0

        self.connectAll()

    def showAbout(self):
        self.aboutDialog = pyVacuumAboutDialog()
        self.aboutDialog.exec_()

    def flashIcon(self):
        self.flash = self.flash ^ 1
        self.connectAction.setIcon(self.flashIcon[self.flash])
        #self.statusBar().showMessage(time.asctime())

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

        # Setup update timer for dumping the widget

        if config.process_image is not None:
            self.dumpWidget()
            self.dumpTimer = QtCore.QTimer(self)
            self.dumpTimer.setInterval(1000 * config.process_image_interval)
            self.connect(self.dumpTimer, QtCore.SIGNAL('timeout()'),
                         self.dumpWidget)
            self.dumpTimer.start()
        else:
            self.dumpTimer = None

        # Load Controllers from Config File

        self.controllers = config.controllers

        # Setup the objects but use no controller when
        # we connect we will call __init__ again!

        self.objects = []
        self.objectinfo = config.guiobjects
        for object in self.objectinfo:
            # Make a copy and set the controller to None
            kwargs = object[1].copy()
            kwargs['controller'] = None
            kwargs['callback'] = self.callbackFromObject
            self.objects.append(object[0](self, **kwargs)) 

        # Setup thread to update the controllers
        self.thread = []
        for c in self.controllers:
            if c is not None:
                if c.needsPolling:
                    self.thread.append(pyVacThread(controller = c))
                    self.thread[-1].start()

    def callbackFromObject(self):
        self.parentWidget().statusBar().showMessage("Last Updated: %s" % time.asctime())

    def disconnectAll(self):
        """
        Disconnect all controllers and stop the thread
        """
        for t in self.thread:
            t.setNoUpdate(True)
            logging.info("disconnectAll() : Stopped controllers thread")

        for c in self.controllers:
            c.close()
            logging.info("disconnectAll() : Closing controller %s" % str(c))

        for o in self.objects:
            o.setController(None)
            o.setDefaultActions()
            logging.info("disconnectAll() : Disconnecting object %s" % str(o))

    def initAll(self):
        flag = False
        for x in range(len(self.controllers)):
            logging.info("initAll() : Trying to initialize controller %d" % x)
            if self.controllers[x] is not None:
                if self.controllers[x].init():
                    logging.info("initAll() : Controller %d initialized" % x)
                else:
                    logging.warning("initAll() : Controller %d (%s) failed to initialize" % 
                                    (x,str(self.controllers[x])))
        return True

    def connectAll(self):
        """ Connect to all controllers and start the thread """
        # Configure Controllers and Objects
        # Stop if we cannot configure 

        self.initAll()

        # Now see what items can be turned on!

        for obj,info in zip(self.objects,self.objectinfo):
            controller = info[1]['controller']
            if type(controller) is not list:
                controller = [controller]
            unit = info[1]['unit']
            if type(unit) is not list:
                unit = [unit]
            flag = True
            for c,u in zip(controller, unit):
                if not c.isInitialized(u):
                    flag = False
                    break
                
            if flag == True:
                # All controllers are init
                obj.setController(controller)
                logging.info("connectAll() : Controller on object %s Initialized OK",str(obj))
                # Add the actions to the devices
                if config.controllable:
                    obj.setActions()
                obj.setCallbacksToControllers()
                # At this point force update
                obj.updateFromController()
            else:
                logging.warning("connectAll() : Failed to initialize controller on %s", obj.getName())

        logging.info("connectAll() : %d controllers configured" % len(self.controllers))
        logging.info("connectAll() %d object configured" % len(self.objects))
        for t in self.thread:
            t.setNoUpdate(False)
        return True

    def dumpWidget(self):

        pixmap = QtGui.QPixmap.grabWidget(self)
        if config.process_image is not None:
            pixmap.save(config.process_image) 

    def updateAll(self):
        # Update all objects by calling update()
        for n in self.objects:
            n.updateFromController()

        # Write a line in the log file

    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        if self.diagram is not None:
            p.drawImage(0, 0, self.diagram)

    
#
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/mainwindow.py $
#
