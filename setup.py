#
# setup.py (c) Stuart B. Wilkins 2008
#
# $Id: setup.py 129 2010-01-27 14:38:33Z swilkins $
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/setup.py $
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

import os
import glob
import PyQt4.pyqtconfig as pyqtconfig
from distutils.core import setup
from distutils.spawn import find_executable, spawn
from distutils.command.build import build
from distutils.command.install import install

def data_files():
    p = "data/*"
    return glob.glob(p)

def qt_ui_files():
    p = "pyVacuum/ui/*.ui"
    return glob.glob(p)

def py_file_name(ui_file):
    return os.path.splitext(ui_file)[0] + '.py'

class pyVacuumBuild(build):
    def compile_ui(self, ui_file):
        pyqt_configuration = pyqtconfig.Configuration()
        pyuic_exe = find_executable('pyuic4', pyqt_configuration.default_bin_dir)
        if not pyuic_exe:
            # Search on the $Path.
            pyuic_exe = find_executable('pyuic4')
        if not pyuic_exe:
	    return
  
        cmd = [pyuic_exe, ui_file, '-o']
	print cmd
        cmd.append(py_file_name(ui_file))
        spawn(cmd)

    def run(self):
        for f in qt_ui_files():
            self.compile_ui(f)

        build.run(self)

setup(name='pyVacuum',
      version='0.1',
      description='Python Object Orientated Control System for Vacuum',
      author='Stuart B. Wilkins',
      author_email='swilkins@bnl.gov',

      packages=['pyVacuum', 'pyVacuum.iomodules', 'pyVacuum.ui'],

      package_data={'pyVacuum': ['images/*.png']},

      #data_files=[('/etc/pyVacuum', data_files())],

      scripts=['scripts/pyVacuum'],
      cmdclass = {
        'build' : pyVacuumBuild}
     )
