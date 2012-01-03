#
# config.py (c) Stuart B. Wilkins 2008
#
# $Id: config.py 104 2009-10-11 21:49:12Z swilkins $
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/config.py $
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

import sys, os, logging, logging.handlers
import os.path
from optparse import OptionParser

#
# First lets parse the commmand line
#

parser = OptionParser()
parser.add_option("-b", "--basename", dest="basename",
                  help="Set basename", metavar="FILE", default = None)

(options, args) = parser.parse_args()

if options.basename is None:
    basename = os.path.basename(sys.argv[0])
else:
    basename = options.basename
    
workingDir = ''

if os.name is 'posix':
    if os.environ.has_key('PYVACUUM'):
        sys.path.append(os.environ['PYVACUUM'])
    else:
        newpath = '/etc/pyVacuum'
        if os.path.exists(newpath):
            print "Adding ", newpath
            sys.path.append('/etc/pyVacuum')
        if os.environ.has_key('HOME'):
            newpath = os.path.join(os.environ['HOME'], ".pyVacuum")
            print "Adding", newpath
            sys.path.append(newpath)
            workingDir = newpath
                
print "Basename =", basename

# Default Values

windowSize = [1000, 800]
graphWindowSize = [1000, 800]

windowTitle = "pyVacuum"
graphWindowTitle = "pyVacuum"

# Default files

backdropFilename = os.path.join(workingDir, basename + ".svg")
logFilename = os.path.join(workingDir, basename + ".log")
valueLogFilename = os.path.join(workingDir, basename + ".dat")
processImageFilename = os.path.join(workingDir, basename + "Process.png")
graphImageFilename = os.path.join(workingDir, basename + "Graph.png")
pickleFilename = os.path.join(workingDir, basename + ".pickle")

# Logging defaults

logLevel = logging.DEBUG
logFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

controllers = []
guiobjects = []

#runpy
exec 'from %sConfig import *' % basename.replace('.py','')

