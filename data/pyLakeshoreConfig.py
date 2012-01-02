#
# pyVacuumConfig-ssh.py (c) Stuart B. Wilkins 2008
#
# $Id: pyVacuumConfig.py 89 2009-01-07 02:21:49Z swilkins $
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

#### DO NOT EDIT BELOW THIS LINE ####

import logging, sys, os
from pyVacuum.iomodules import lakeshore
import pyVacuum.iomodules.eurotherm as eurotherm
from pyVacuum import objects

#### Edit Below This Line ###########

windowSize = [500, 200]
windowTitle = "Lakeshore"

graphWindowSize = [800, 500]
graphWindowTitle = "Lakeshore Graph"

backdropFilename = None

# Log and level
# Setting to debug will create a LOT of text!
# Levels are 
# CRITICAL, ERROR, WARNING, INFO, DEBUG and UNSET.

logFilename = None
loglevel = logging.INFO
#logFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


# Textfile for values log

valueLogFilename = None
valueLogSep = ","
valueLogFormat = "%10.8e"
valueLogStringFormat = "%12s"

# Interval at which to log 
logInterval = 10

# Interval to update display
timerInterval = 5 * 1000

# Ringbuffer length (number of intervals)
ringbufferLen = 60 * 60 * 24

# Setup remote process image

processImageFilename = None
#processImageFilename = "/var/www/external/vacuum/VacProcessImage.png"
#processImageFilename = workingDir + name + "Process.png"

# Setup remote graph image

graphImage = None
#graphImageFilename = "/var/www/external/vacuum/VacGraph.png"

# Now setup the controllers

controllers = [
    lakeshore.Lakeshore(host = ('10.0.27.52', 3004))
    ]


guiobjects = [
    [ objects.pyVacLCD,      {'name' : "Setpoint",
                              'controller' : controllers[0],
                              'unit' : 0,
                              'x' : 310,
                              'y' : 70 }],
    [ objects.pyVacLCD,      {'name' : "Regulation",
                              'controller' : controllers[0],
                              'unit' : 1,
                              'x' : 70,
                              'y' : 70 }],
    [ objects.pyVacLCD,      {'name' : "Sample",
                              'controller' : controllers[0],
                              'unit' : 2,
                              'x' : 190,
                              'y' : 70 }],
    [ objects.pyVacLCD,      {'name' : "Heater",
                              'controller' : controllers[0],
                              'unit' : 11,
                              'x' : 430,
                              'y' : 70 }]
    ]


#
# $HeadURL: svn+ssh://swilkins@solids.phy.bnl.gov/home/swilkins/.svnrepos/pyVacuum/examples/pyVacuumConfig.py $
#                                        
