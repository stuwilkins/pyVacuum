#
# log.py (c) Stuart B. Wilkins 2008
#
# $Id: wago.py 106 2009-10-12 00:16:17Z swilkins $
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/iomodules/wago.py $
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

import logging as log
import config

def setupLog(name):
    logging = log.getLogger(name)
    logging.setLevel(log.WARN)
    ch = log.StreamHandler()
    ch.setLevel(log.WARN)
    formatter = log.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logging.addHandler(ch)
    return logging
