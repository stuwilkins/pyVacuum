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

windowSize = [1250, 700]
windowTitle = "TARDIS Vacuum Control"

graphWindowSize = [800, 500]
graphWindowTitle = "pyVacuum Graph"

backdropFilename = "/etc/pyVacuum/pyVacuum.svg"

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

processImageFilename = "/var/www/external/vacuum/VacProcessImage.png"
#processImageFilename = workingDir + name + "Process.png"

# Setup remote graph image

#graphImage = None
graphImageFilename = "/var/www/external/vacuum/VacGraph.png"

# Now setup the controllers

controllers = [
    varianmg.VarianMGVac(    ("10.0.27.52", 3000), 
                             mode = varianmg.VarianMGVac.SOCKET),
    varianmg.VarianMGVac(    ("10.0.27.52", 3001), 
                             mode = varianmg.VarianMGVac.SOCKET),
    gammampc.GammaMPC(       ("10.0.27.52", 3002)),
    wago.WagoValve(          ("10.0.27.52", 502), 
                             opaddr = [0, 1, 2, 3, 4, 5, 6, 7, 18, 20, 22], 
                             ipaddr = [0, 2, 4, 6, 8, 10, 12, 14, 34, 36, 38],
                             mode =   [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1]),
    wago.STP451Turbo(        ("10.0.27.52", 502), [8], [16]),
    wago.WagoBackPump(       ("10.0.27.52", 502), [14, 13, 12]),
    wago.NT10Turbo(          ("10.0.27.52", 502), [16], [21])]


guiobjects = [
    [ objects.pyVacChamber,{'name' : "MAIN CHAMBER",
                            'controller' : [controllers[0], 
                                            controllers[0], 
                                            controllers[0]], 
                            'unit' : [2, 3, 0],
                            'x' : 430, 
                            'y' : 30, 
                            'width' : 240, 
                            'height' : 540 }],
    [ objects.pyVacChamber,{'name' : "Load Lock",
                            'controller' : [controllers[1],
                                            controllers[1]], 
                            'unit' : [2, 0],
                            'x' : 790, 
                            'y' : 350, 
                            'width' : 240, 
                            'height' : 220 }],
    [ objects.pyVacValve, {'name' : "VALVE 1",
                                   'controller' : controllers[3],
                                   'unit' : 0,
                                   'x' : 370,
                                   'y' : 500 }],
    #[ objects.pyVacValve, {'name' : "VALVE 2",
    #                               'controller' : controllers[3],
    #                               'unit' : 1,
    #                               'x' : 370,
    #                               'y' : 400 }],
    [ objects.pyVacValve, {'name' : "VALVE 3",
                                   'controller' : controllers[3],
                                   'unit' : 2,
                                   'x' : 370,
                                   'y' : 362 }],
    [ objects.pyVacValve, {'name' : "VALVE 4",
                                   'controller' : controllers[3],
                                   'unit' : 3,
                                   'x' : 370,
                                   'y' : 200 }],
    [ objects.pyVacValve, {'name' : "VALVE 7",
                                   'controller' : controllers[3],
                                   'unit' : 6,
                                   'x' : 730,
                                   'y' : 250 }],
    [ objects.pyVacValve, {'name' : "VALVE 5",
                                   'controller' : controllers[3], 
                                   'unit' : 4,
                                   'x' : 730, 
                                   'y' : 500 }],
    [ objects.pyVacValve, {'name' : "VALVE 6",
                                   'controller' : controllers[3], 
                                   'unit' : 5,
                                   'x' : 1090, 
                                   'y' : 400 }],
    #[ objects.pyVacValve, {'name' : "V11i",
    #                               'controller' : controllers[3], 
    #                               'unit' : 8,
    #                               'x' : 370, 
    #                               'y' : 75 }],
    #[ objects.pyVacValve, {'name' : "V10i",
    #                               'controller' : controllers[3], 
    #                               'unit' : 9,
    #                               'x' : 270, 
    #                               'y' : 75 }],
    #[ objects.pyVacValve, {'name' : "V09i",
    #                               'controller' : controllers[3], 
    #                               'unit' : 10,
    #                               'x' : 170, 
    #                               'y' : 75 }],
    [ objects.pyVacPump,  {'name' : "IONP1",
                           'controller' : controllers[2], 
                           'unit' : 0,
                           'x' : 60, 
                           'y' : 500, 
                           'port' : objects.pyVacPump.RIGHT,
                           'type' : objects.pyVacPump.ION }],
    [ objects.pyVacGauge, {'name' : "IONP1",
                           'controller' : controllers[2], 
                           'unit' : 16,
                           'x' : 120, 
                           'y' : 475 }],
    [ objects.pyVacPump,  {'name' : "IONP2",
                           'controller' : controllers[2], 
                           'unit' : 1,
                           'x' : 60, 
                           'y' : 362, 
                           'port' : objects.pyVacPump.RIGHT,
                           'type' : objects.pyVacPump.ION }],
    [ objects.pyVacGauge, {'name' : "IONP2",
                           'controller' : controllers[2], 
                           'unit' : 17,
                           'x' : 120, 
                           'y' : 337 }],
    [ objects.pyVacPump,  {'name' : "TURBO 1",
                           'controller' : controllers[4], 
                           'unit' : 0,
                           'x' : 260, 
                           'y' : 200, 
                           'type' : objects.pyVacPump.TURBO,
                           'port' : objects.pyVacPump.RIGHT | 
                           objects.pyVacPump.LEFT }],
     [ objects.pyVacPump,  {'name' : "TURBO 2",
                           'controller' : controllers[6], 
                           'unit' : 0,
                           'x' : 1090, 
                           'y' : 500, 
                           'type' : objects.pyVacPump.TURBO,
                           'port' : objects.pyVacPump.RIGHT | 
                           objects.pyVacPump.LEFT }],
    [ objects.pyVacPump,  {'name' : "ROUGH 1",
                           'controller' : controllers[5], 
                           'unit' : 0,
                           'x' : 60, 
                           'y' : 200, 
                           'port' : objects.pyVacPump.RIGHT,
                           'type' : objects.pyVacPump.ROUGH }],
    [ objects.pyVacGauge, {'name' : "TC3",
                           'controller' : controllers[0],
                           'unit' : 1,
                           'x' : 120,
                           'y' : 175}],
    [ objects.pyVacGauge, {'name' : "TC1",
                           'controller' : controllers[0], 
                           'unit' : 0,
                           'x' : 725, 
                           'y' : 150 }],
    [ objects.pyVacGauge, {'name' : "IONG1",
                           'controller' : controllers[0], 
                           'unit' : 2,
                           'x' : 875,
                           'y' : 150 }],
    [ objects.pyVacGauge, {'name' : "IMG1",
                           'controller' : controllers[0], 
                           'unit' : 3,
                           'x' : 1025, 
                           'y' : 150 }],
    [ objects.pyVacGauge, {'name' : "IONG2",
                           'controller' : controllers[1], 
                           'unit' : 2,
                           'x' : 950,
                           'y' : 340 }],
    [ objects.pyVacGauge, {'name' : "TC2",
                           'controller' : controllers[1], 
                           'unit' : 0,
                           'x' : 810, 
                           'y' : 340 }],
    [ objects.pyVacPump,  {'name' : "ROUGH 2",
                           'controller' : controllers[5], 
                           'unit' : 1,
                           'x' : 1200, 
                           'y' : 500, 
                           'port' : objects.pyVacPump.LEFT,
                           'type' : objects.pyVacPump.ROUGH }],
    #[ objects.pyVacGauge, {'name' : "TC 3",
    #                       'controller' : controllers[1], 
    #                       'unit' : 0,
    #                       'x' : 135, 
    #                       'y' : 85 }],
    #[ objects.pyVacSensor,{'name' : "THERMO 1",
    #                       'controller' : controllers[5], 
    #                       'unit' : 0,
    #                       'x' : 1000, 
    #                       'y' : 100, 
    #                       'format' : "%5.2f" }],
    #[ objects.pyVacSensor,{'name' : "THERMO 2",
    #                       'controller' : controllers[5], 
    #                       'unit' : 1,
    #                       'x' : 1000, 
    #                       'y' : 200, 
    #                       'format' : "%5.2f" }],
    #[ objects.pyVacSensor,{'name' : "THERMO 3", 
    #                       'controller' : controllers[8], 
    #                       'unit' : 2,
    #                       'x' : 1000, 
    #                       'y' : 300,
    #                       'format' : "%5.2f"}]
]


#
# $HeadURL: svn+ssh://swilkins@solids.phy.bnl.gov/home/swilkins/.svnrepos/pyVacuum/examples/pyVacuumConfig.py $
#                                        
