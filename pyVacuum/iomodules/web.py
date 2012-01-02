#
# web.py (c) Stuart B. Wilkins 2008
#
# $Id: web.py 65 2009-01-02 03:13:04Z swilkins $
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
import httplib

from objects import *

import logging as log
#log.basicConfig(stream = sys.stderr, level = log.DEBUG)
logging = log.getLogger(__name__)

class webImage(VacObject):
    ALLIMAGE = "Status/images/ringstat.gif"
    XIMAGE = "Status/images/Xstat.gif"
    def __init__(self, host = "status.nsls.bnl.gov", path = XIMAGE):
        if type(host) == type(""):
            self.host = (host, 80)
        else:
            self.host = host

        self.path = path
        
        self.status = self.ON
        self.image = ""

    def update(self):
        h = httplib.HTTPConnection(self.host[0], self.host[1])
        h.request("GET", "/%s" % self.path)
        r = h.getresponse()
        if r.status != 200:
            logging.warning("Failed to connect to %s reason = %s" %
                            (self.host, r.reason)) 
            return False
        
        self.image = r.read()
        return True

    def getImage(self):
        return self.image
