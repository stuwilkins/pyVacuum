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
from pyVacuum.iomodules import varianmg, gammampc, wago, nsls
import pyVacuum.iomodules.eurotherm as eurotherm
from pyVacuum import objects

#### Edit Below This Line ###########

windowSize = [600, 350]
windowTitle = "X1A2 Beamline Control"

graphWindowSize = [800, 500]
graphWindowTitle = "pyBeamline Graph"

backdropFilename = "/etc/pyVacuum/pyBeamline.svg"

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
timerInterval = 1 * 1000

# Ringbuffer length (number of intervals)
ringbufferLen = 60 * 60 * 24

# Setup remote process image

#processImageFilename = "/var/www/external/vacuum/VacProcessImage.png"
#processImageFilename = workingDir + name + "Process.png"

# Setup remote graph image

#graphImage = None
#graphImageFilename = "/var/www/external/vacuum/VacGraph.png"

# Now setup the controllers

controllers = [
    wago.WagoValve(          ("10.0.0.101", 502), 
                             opaddr = [18, 20, 22, None], 
                             ipaddr = [34, 36, 38, 32],
                             mode =   [ 1,  1,  1, 2]),
    nsls.NSLSRingStatus(),
    wago.WagoDigit(          ("10.0.0.101", 502),
                             ipaddr = [[0x0200 + 16], [26, 27]],
                             mode = ['', 'or'])
    ]


guiobjects = [
    [ objects.pyVacValve,    {'name' : "V11i",
                              'controller' : controllers[0], 
                              'unit' : 0,
                              'x' : 500, 
                              'y' : 175 }],
    [ objects.pyVacValve,    {'name' : "V10i",
                              'controller' : controllers[0], 
                              'unit' : 1,
                              'x' : 400, 
                              'y' : 175 }],
    [ objects.pyVacValve,    {'name' : "V09i",
                              'controller' : controllers[0], 
                              'unit' : 2,
                              'x' : 300, 
                              'y' : 175 }],
    [ objects.pyVacValve,    {'name' : "X1 Shutter",
                              'controller' : controllers[0], 
                              'unit' : 3,
                              'x' : 70, 
                              'y' : 175 }],
    [ objects.pyVacLCD,      {'name' : "NSLS Curr.",
                              'controller' : controllers[1],
                              'unit' : 0,
                              'x' : 70,
                              'y' : 70 }],
    [ objects.pyVacIndicator, {'name' : "NSLS Stat.",
                               'controller' : controllers[1],
                               'unit' : 0,
                               'x' : 300,
                               'y' : 70 ,
                               'statustext' : ['ERR', 'BEAM', 'NOBEAM']}],
    [ objects.pyVacIndicator, {'name' : "BL Itlk",
                               'controller' : controllers[2],
                               'unit' : 0,
                               'x' : 400,
                               'y' : 70,
                               'statustext' : ['ERR', 'GOOD', 'FAULT']}],
    [ objects.pyVacIndicator, {'name' : "Vac Itlk",
                               'controller' : controllers[2],
                               'unit' : 1,
                               'x' : 500,
                               'y' : 70,
                               'statustext' : ['ERR', 'GOOD', 'FAULT']}]
    ]


#
# $HeadURL: svn+ssh://swilkins@solids.phy.bnl.gov/home/swilkins/.svnrepos/pyVacuum/examples/pyVacuumConfig.py $
#                                        
