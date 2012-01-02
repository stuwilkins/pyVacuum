#
# pyVacuumConfig-ssh.py (c) Stuart B. Wilkins 2008
#
# $Id: nslsstatusConfig.py 65 2009-01-02 03:13:04Z swilkins $
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
from iomodules import web
from pyVacuum import objects

#### Edit Below This Line ###########

windowSize = [750, 600]
windowTitle = "TARDIS Vacuum Control"

graphWindowSize = [800, 500]
graphWindowTitle = "pyVacuum Graph"


# Log and level
# Setting to debug will create a LOT of text!
# Levels are 
# CRITICAL, ERROR, WARNING, INFO, DEBUG and UNSET.

loglevel = logging.INFO

# Textfile for values log

valueLogSep = ","
valueLogFormat = "%10.8e"
valueLogStringFormat = "%12s"

# Interval at which to log 
logInterval = 10

# Interval to update display
timerInterval = 1 * 1000

# Ringbuffer length (number of intervals)
ringbufferLen = 60 * 60 * 24

# Now setup the controllers

controllers = [ 
    web.webImage(host = "status.nsls.bnl.gov", path = "Status/images/Xstat.gif")
]

guiobjects = [
    [ objects.pyVacWebImage, {'name' : "NSLS Status",
                                'controller' : controllers[0],
                                'unit' : 0,
                                'x' : 0,
                                'y' : 0,
                                'width' : 750,
                                'height' : 1000}],
]

#
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/examples/nslsstatusConfig.py $
#                                        
