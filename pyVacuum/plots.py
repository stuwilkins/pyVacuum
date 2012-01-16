#
# objects.py (c) Stuart B. Wilkins 2008
#
# $Id: objects.py 122 2009-10-26 10:50:50Z swilkins $
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/objects.py $
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
import math
import numpy
import time
import os

from PyQt4 import Qt, QtCore, QtGui

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from matplotlib.backend_bases import cursors

cursord = {
    cursors.MOVE          : QtCore.Qt.SizeAllCursor,
    cursors.HAND          : QtCore.Qt.PointingHandCursor,
    cursors.POINTER       : QtCore.Qt.ArrowCursor,
    cursors.SELECT_REGION : QtCore.Qt.CrossCursor,
}

class NavigationToolbarCustom(NavigationToolbar):
    def __init__(self, *args, **kwargs):
        pixmap = QtGui.QPixmap()
        pixmap.load(':/cross.png')
        cursors.SELECT_POINT = pixmap
        super(NavigationToolbar, self).__init__(*args, **kwargs)

    def _init_toolbar(self):
        self.basedir = os.path.join(matplotlib.rcParams[ 'datapath'
],'images')

        a = self.addAction(self._icon('home.svg'), 'Home', self.home)
        a.setToolTip('Reset original view')

        self.addSeparator()

        a = self.addAction(self._icon('move.svg'), 'Pan', self.pan)
        a.setToolTip('Pan axes with left mouse, zoom with right')

        a = self.addAction(self._icon('zoom_to_rect.svg'), 'Zoom',
                           self.zoom)
        a.setToolTip('Zoom to rectangle')

        #a = self.addAction(self._icon('hand.svg'), 'Select',
        #                   self.pan)
        #a.setToolTip('Select the nearest data point')

        self.addSeparator()

        a = self.addAction(self._icon('filesave.svg'), 'Save',
                           self.save_figure)
        a.setToolTip('Save the figure')

        self.buttons = {}

        # Add the x,y location widget at the right side of the toolbar
        # The stretch factor is 1 which means any resizing of the toolbar
        # will resize this label instead of the buttons.
        if self.coordinates:
            self.locLabel = QtGui.QLabel( "", self )
            self.locLabel.setAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignTop )
            self.locLabel.setSizePolicy(
                QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                  QtGui.QSizePolicy.Ignored))
            labelAction = self.addWidget(self.locLabel)
            labelAction.setVisible(True)

    def selectPoint(self, event):
        if event.inaxes and event.inaxes.get_navigate():
            self.xdatastart=event.xdata
            self.ydatastart=event.ydata
            self.xstart=event.x
            self.ystart=event.y
            self._banddraw = self.canvas.mpl_connect(
                'motion_notify_event',self.drawband)
            self._idRelease = self.canvas.mpl_disconnect(self._idRelease)
            self._idRelease = self.canvas.mpl_connect(
                'button_release_event', self.selectSecondPoint)
            

    def selectSecondPoint(self, event):
        if event.inaxes and event.inaxes.get_navigate():
            self._banddraw=self.canvas.mpl_disconnect(self._banddraw)
            self._idRelease = self.canvas.mpl_disconnect(self._idRelease)
            self._idRelease = self.canvas.mpl_connect(
                'button_press_event', self.selectPoint)
            self.draw_rubberband(event, 0, 0, 0, 0)

            self.zoomArea = [self.xdatastart, event.xdata,
                             self.ydatastart, event.ydata]

            print self.zoomArea

    def drawband(self, event):
        self.draw_rubberband(event,self.xstart, self.ystart, 
                             event.x, event.y)

    def home(self):
        print "HOME"

    def pan(self):
        print "PAN" 

    def zoom(self):
        print "ZOOM"
        self.set_cursor(cursors.SELECT_REGION)
        self._idRelease = self.canvas.mpl_connect('button_press_event', self.selectPoint)
        

class CCDTwoDPlot(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        QtGui.QWidget.__init__(self, *args, **kwargs)
        self.fig = Figure((6.5,6.5), dpi = 100)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.axes = self.fig.add_axes([0.2,0.175,0.75,0.75],axisbg='k')
        self.axesl = self.fig.add_axes([0.075,0.175,0.10,0.75],axisbg='k')
        self.axesb = self.fig.add_axes([0.2,0.05,0.75,0.10],axisbg='k')
        self.mpl_toolbar = NavigationToolbarCustom(self.canvas, self)
        #self.canvas.mpl_connect('button_press_event',self.buttonPressed)
        #self.canvas.mpl_connect('button_release_event', self.buttonReleased)

        self.imageCtr = (-1,-1)
        
        self.showCrosshairs = False
        self.mouseMode = 'pick'
        self.fullImage = None
        self.image = None

    def setImage(self, image):
        """Set the 2D numpy array of the image"""
        self.fullImage = image
        if self.image is None:
            self.resetFullImage()
        else:
            self.setRoi()

    def setRoi(self):
        try:
            self.image = self.fullImage[int(self.currentRoi[0]):int(self.currentRoi[1]),
                                        int(self.currentRoi[2]):int(self.currentRoi[3])]
        except:
            self.image = self.fullImage

    def resetFullImage(self):
        self.image = self.fullImage
        self.currentRoi = [0,self.image.shape[0],0,self.image.shape[1]]

    def update(self):

        self.axes.clear()

        vmin, vmax = self.autoScaleImage()
        
        self.axes.imshow(self.image, vmin = vmin, 
                         vmax = vmax,
                         extent = self.currentRoi)
        self.forceAspect()

        cpointx = self.imageCtr[0]
        if (cpointx < 0) or (cpointx >= self.image.shape[0]):
            cpointx = self.image.shape[0] / 2.0
        cpointy = self.imageCtr[1]
        if (cpointy < 0) or (cpointy >= self.image.shape[1]):
            cpointy = self.image.shape[1] / 2.0
            
        lv = self.image[:,int(cpointx)]
        bv = self.image[int(cpointy),:]

        if self.showCrosshairs:
            self.axes.axhline(cpointy, linewidth = 0.5, color = 'k')
            self.axes.axvline(cpointx, linewidth = 0.5, color = 'k')

        self.axes.xaxis.set_ticklabels([])
        self.axes.yaxis.set_ticklabels([])

        self.axesl.clear()
        self.axesl.plot(lv,range(self.currentRoi[0],self.currentRoi[1]),'r-')
        self.axesl.set_xlim([vmin, vmax])
        self.axesl.set_ylim(self.currentRoi[0:2][::-1])
        
        self.axesb.clear()
        self.axesb.plot(range(self.currentRoi[2],self.currentRoi[3]),bv,'r-')
        self.axesb.set_xlim(self.currentRoi[2:4])
        self.axesb.set_ylim([vmin, vmax])
        self.axesl.xaxis.set_major_locator(MaxNLocator(3))
        self.axesb.yaxis.set_major_locator(MaxNLocator(3))

        self.canvas.draw()

    def buttonPressed(self,event):
        if event.inaxes == self.axes:
            if self.mouseMode == 'pick':
                self.imageCtr = event.xdata, event.ydata
                self.showCrosshairs = True
                self.update()
            elif self.mouseMode == 'zoom':
                self.zoomStart = event.xdata, event.ydata

    def buttonReleased(self,event):
        if event.inaxes == self.axes:
            if self.mouseMode == 'zoom':
                self.zoomEnd = event.xdata, event.ydata
                roi = []
                for start,end in zip(self.zoomStart, self.zoomEnd):
                    if start < end:
                        roi += [int(start), int(end)]
                    else:
                        roi += [int(end),int(start)]

                self.currentRoi = roi
                print self.currentRoi
                self.setRoi()
                self.update()

    def autoScaleImage(self, lwr = 5, upr = 95):
        """Return the min and max values"""
        s = numpy.sort(numpy.ravel(self.image))
        l = s[int(lwr*len(s)/100.0)]
        u = s[int(upr*len(s)/100.0)]
        return l,u

    def forceAspect(self, aspect = 1.0):
        extent = self.currentRoi
        dataAspect = abs(float(extent[1]-extent[0])/float(extent[3]-extent[2]))/aspect
        if dataAspect:
            self.axes.set_aspect(dataAspect)
