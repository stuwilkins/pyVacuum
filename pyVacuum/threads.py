#!/usr/bin/python
#
# threads.py (c) Stuart B. Wilkins 2008
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

import time
import threading
import sys

import config

# Setup Log

import logging as log
logging = log.getLogger(__name__)

class pyVacThread(threading.Thread):
    def __init__(self, controller = None, objects = None):
        threading.Thread.__init__(self)
        self.sleep_interval = 1
        self.finished = threading.Event()
        self.controller = controller
        self.objects = objects
        self.updateTime = "Never"
        self.noupdate = True

    def setNoUpdate(self, b):
        self.noupdate = b

    def stop(self):
        self.finished.set()
        self.join()        

    def lastUpdated(self):
        return self.updateTime

    def run (self): 
        logging.debug("Starting Update Thread %s" % self.controller)
        while not self.finished.isSet():
            self.finished.wait(self.sleep_interval)
            if not self.noupdate:
                try:
                    self.controller.update()
                except:
                    logging.critical("Failed update : %s %s" % (sys.exc_info()[0:2]))

                self.updateTime = time.asctime()
            else:
                self.updateTime = "Never"
                
