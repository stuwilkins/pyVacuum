#!/usr/bin/python
#
# textupdate.py (c) Stuart B. Wilkins 2008
#
# $Id: mainwindow.py 93 2009-01-19 00:25:31Z swilkins $
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
import signal

# Setup Log
import logging as log
logging = log.getLogger(__name__)

# Config info
 
from pyVacuum.iomodules.objects import * 
import pyVacuum
from pyVacuum import ringbuffer

from pyVacuum import config

from threads import *

def signalHandler(signum, frame):
    print "Signal captured"

def mainLoop():
    controllers = config.controllers
    objectinfo = config.guiobjects

    # Setup handlers

    signal.signal(signal.SIGINT, signalHandler)

    # Initialize all Controllers

    for c in controllers:
        c.init()

    thread = []
    for c in controllers:
        thread.append(pyVacThread(controller = c))
        thread[-1].start()
        thread[-1].setNoUpdate(False)

    print "Started all controllers"

    while 1:
        for o in objectinfo:
            c = o[1]['controller']
            u = o[1]['unit']
            if type(c) != type([]):
                if c is not None:
                    if c.isInitialized(u):
                        try:
                            print o[1]['name'], c.getValue(u), c.getStatusMessage(u)
                        except:
                            pass
        time.sleep(10)
                        
if __name__ == "__main__":
    mainLoop()
