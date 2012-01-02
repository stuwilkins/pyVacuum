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

windowSize = [1100, 700]
windowTitle = "TARDIS Vacuum Control"

graphWindowSize = [800, 500]
graphWindowTitle = "pyVacuum Graph"

# Log and level
# Setting to debug will create a LOT of text!
# Levels are 
# CRITICAL, ERROR, WARNING, INFO, DEBUG and UNSET.

#logFilename = None
loglevel = logging.INFO
#logFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


# Textfile for values log

#valueLogFilename = None
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

#processImageFilename = None
#processImageFilename = workingDir + name + "Process.png"

# Setup remote graph image

#graphImage = None
#graphImageFilename = workingDir + name + "Graph.png"

# Now setup the controllers

controllers = [
    varianmg.VarianMGVac(    ("localhost", 3000), 
                             mode = varianmg.VarianMGVac.SOCKET),
    varianmg.VarianMGVac(    ("localhost", 3001), 
                             mode = varianmg.VarianMGVac.SOCKET),
    gammampc.GammaMPC(       ("localhost", 3002)),
    wago.WagoValve(          ("localhost", 3003), 
                             opaddr = [0, 1, 2, 3], 
                             ipaddr = [0, 2, 4, 6]),
    wago.STP451Turbo(        ("localhost", 3003), [4], [8]),
    wago.WagoSensor(         ("localhost", 3003), [0, 1], 
                             type = wago.WagoSensor.TYPEK469),
    nsls.NSLSRingStatus(     ring = "XRAY"),
    wago.WagoBackPump(       ("localhost", 3003), [6, 7]),
    eurotherm.Eurotherm2000(("localhost", 4001), unit = 2)]

guiobjects = [
    [ objects.pyVacValve, {'name' : "VALVE 1",
                                   'controller' : controllers[3],
                                   'unit' : 0,
                                   'x' : 370,
                                   'y' : 500 }],
    [ objects.pyVacValve, {'name' : "VALVE 4",
                                   'controller' : None, 
                                   'unit' : None,
                                   'x' : 750, 
                                   'y' : 167, 
                                   'type' : objects.pyVacValve.MANUAL}],
    [ objects.pyVacPump,  {'name' : "IONP 1",
                                   'controller' : controllers[2], 
                                   'unit' : 0,
                                   'x' : 210, 
                                   'y' : 500, 
                                   'port' : objects.pyVacPump.RIGHT,
                                   'type' : objects.pyVacPump.ION }],
    [ objects.pyVacGauge, {'name' : "IONP 1",
                                   'controller' : controllers[2], 
                                   'unit' : 16,
                                   'x' : 290, 
                                   'y' : 450 }],
    [ objects.pyVacValve, { 'name' : "VALVE 3",
                                    'controller' : controllers[3], 
                                    'unit' : 2,
                                    'x' : 750, 
                                    'y' : 500 }],
    [ objects.pyVacPump,  {'name' : "IONP 2",
                           'controller' : controllers[2], 
                           'unit' : 1,
                           'x' : 910, 
                           'y' : 500, 
                           'port' : objects.pyVacPump.LEFT,
                           'type' : objects.pyVacPump.ION }],
    [ objects.pyVacGauge, {'name' : "IONP 2",
                           'controller' : controllers[2], 
                           'unit' : 17,
                           'x' : 830, 
                           'y' : 450 }],
    [ objects.pyVacValve, {'name' : "VALVE 2",
                           'controller' : controllers[3], 
                           'unit' : 1,
                           'x' : 370, 
                           'y' : 250 }],
    [ objects.pyVacPump,  {'name' : "TURBO 1",
                           'controller' : controllers[4], 
                           'unit' : 0,
                           'x' : 210, 
                           'y' : 250, 
                           'type' : objects.pyVacPump.TURBO,
                           'port' : objects.pyVacPump.RIGHT | 
                           objects.pyVacPump.LEFT }],
    [ objects.pyVacPump,  {'name' : "ROUGH 1",
                           'controller' : controllers[7], 
                           'unit' : 0,
                           'x' : 60, 
                           'y' : 250, 
                           'port' : objects.pyVacPump.RIGHT,
                           'type' : objects.pyVacPump.ROUGH }],
    [ objects.pyVacGauge, {'name' : "TC 1",
                           'controller' : controllers[0], 
                           'unit' : 0,
                           'x' : 135, 
                           'y' : 200 }],
    [ objects.pyVacGauge, {'name' : "TC 2",
                           'controller' : controllers[0], 
                           'unit' : 1,
                           'x' : 825, 
                           'y' : 150 }],
    [ objects.pyVacGauge, {'name' : "IONG 1",
                           'controller' : controllers[0], 
                           'unit' : 2,
                           'x' : 725,
                           'y' : 325 }],
    [ objects.pyVacGauge, {'name' : "CC 1",
                           'controller' : controllers[1], 
                           'unit' : 4,
                           'x' : 725, 
                           'y' : 400 }],
    [ objects.pyVacPump,  {'name' : "ROUGH 2",
                           'controller' : controllers[7], 
                           'unit' : 1,
                           'x' : 60, 
                           'y' : 100, 
                           'port' : objects.pyVacPump.RIGHT,
                           'type' : objects.pyVacPump.ROUGH }],
    [ objects.pyVacGauge, {'name' : "TC 3",
                           'controller' : controllers[1], 
                           'unit' : 0,
                           'x' : 135, 
                           'y' : 85 }],
    [ objects.pyVacSensor,{'name' : "THERMO 1",
                           'controller' : controllers[5], 
                           'unit' : 0,
                           'x' : 1000, 
                           'y' : 100, 
                           'format' : "%5.2f" }],
    [ objects.pyVacSensor,{'name' : "THERMO 2",
                           'controller' : controllers[5], 
                           'unit' : 1,
                           'x' : 1000, 
                           'y' : 200, 
                           'format' : "%5.2f" }],
    [ objects.pyVacSensor,{'name' : "THERMO 3", 
                           'controller' : controllers[8], 
                           'unit' : 2,
                           'x' : 1000, 
                           'y' : 300,
                           'format' : "%5.2f"}],
    [ objects.pyVacChamber,{'name' : "MAIN CHAMBER",
                            'controller' : [controllers[0], 
                                            controllers[1], 
                                            controllers[0]], 
                            'unit' : [2, 4, 1],
                            'x' : 430, 
                            'y' : 130, 
                            'width' : 240, 
                            'height' : 440 }]
]


#
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/examples/pyVacuumConfig.py $
#                                        
