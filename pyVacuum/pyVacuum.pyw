#!/usr/bin/python
#
# pyVacuum.py (c) Stuart B. Wilkins 2008
#
# $Id: pyVacuum 65 2009-01-02 03:13:04Z swilkins $
# $HeadURL: svn+ssh://solids/home/swilkins/.svnrepos/pyVacuum/scripts/pyVacuum $
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

import sys
import os.path
from pyVacuum import mainwindow
from PyQt4 import QtCore, QtGui

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    apppath = sys.argv[0]
    print "Run as :", os.path.basename(apppath)
    myapp = mainwindow.pyVacWindow(appname = os.path.basename(apppath))
    myapp.show()
    sys.exit(app.exec_())
