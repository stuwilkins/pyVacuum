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

        self.plot = args[1]

    def _init_toolbar(self):
        self.setIconSize(QtCore.QSize(20,20))

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

        a = self.addAction(self._icon('hand.svg'), 'Select',
                           self.pan)
        a.setToolTip('Select center for lineouts')

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
            self.zoomStart=[event.xdata, event.ydata]
            
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
            self.zoomEnd = [event.xdata, event.ydata]
            for s,e in zip(self.zoomStart,self.zoomEnd):
                if abs(e-e):
                    return
            self.plot.setRoi(self.zoomStart, self.zoomEnd)

    def drawband(self, event):
        self.draw_rubberband(event,self.xstart, self.ystart, 
                             event.x, event.y)

    def home(self):
        self.plot.resetFullImage()

    def pan(self):
        self._idRelease = self.canvas.mpl_disconnect(self._idRelease)
        self._idRelease = self.canvas.mpl_connect(
            'button_release_event', self.selectCtr)

    def selectCtr(self,event):
        self.plot.setImageCtr(event.xdata,event.ydata)
        self._idRelease = self.canvas.mpl_disconnect(self._idRelease)

    def zoom(self):
        self.set_cursor(cursors.SELECT_REGION)
        self._idRelease = self.canvas.mpl_connect('button_press_event', self.selectPoint)

class CCDTwoDPlot(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        QtGui.QWidget.__init__(self, *args, **kwargs)
        bgcol = str(self.palette().background().color().name())
        self.fig = Figure((6,6), dpi = 100, facecolor = bgcol)
        
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.axes = self.fig.add_axes([0.2,0.175,0.725,0.725],axisbg='k')
        self.axesl = self.fig.add_axes([0.075,0.175,0.125,0.725],axisbg='k')
        self.axesb = self.fig.add_axes([0.2,0.05,0.725,0.125],axisbg='k')

        for ax in self.axes,self.axesl,self.axesb:
             ax.xaxis.set_ticklabels([])
             ax.axes.yaxis.set_ticklabels([])
        
        self.mpl_toolbar = NavigationToolbarCustom(self.canvas, self)

        # Setup move connection

        self.canvas.mpl_connect('motion_notify_event', self.motionNotify)

        # Setup defaults

        self.title = None

        # Setup widgets for controls

        self.groupBox = QtGui.QGroupBox("Image Controls", self)
        self.groupBox.move(610,0)
        self.groupBox.resize(175,600)
        self.groupBox.show()

        self.autoScaleButtons = [QtGui.QRadioButton("Autoscale 10/90%", self.groupBox)]
        self.autoScaleButtons[-1].move(5,70)
        self.autoScaleButtons[-1].setChecked(True)
        self.autoScaleButtons.append(QtGui.QRadioButton("Autoscale 5/95%", self.groupBox))
        self.autoScaleButtons[-1].move(5,100)
        self.autoScaleButtons.append(QtGui.QRadioButton("Autoscale 2/98%", self.groupBox))
        self.autoScaleButtons[-1].move(5,130)
        self.autoScaleButtons.append(QtGui.QRadioButton("Autoscale 1/99%", self.groupBox))
        self.autoScaleButtons[-1].move(5,160)
        self.autoScaleButtons.append(QtGui.QRadioButton("Autoscale Full", self.groupBox))
        self.autoScaleButtons[-1].move(5,190)
        self.autoScaleButtons.append(QtGui.QRadioButton("Manual", self.groupBox))
        self.autoScaleButtons[-1].move(5,220)

        for button in self.autoScaleButtons:
            self.connect(button,QtCore.SIGNAL('clicked()'),
                         self.update)

        self.manualScaleLwrLabel = QtGui.QLabel("Lower Level (%)", self.groupBox)
        self.manualScaleLwrLabel.move(5,260)
        self.manualScaleLwrLabel.resize(130,25)
        self.manualScaleUprLabel = QtGui.QLabel("Lower Level (%)", self.groupBox)
        self.manualScaleUprLabel.move(5,310)
        self.manualScaleUprLabel.resize(130,25)
        self.manualScaleLwr = QtGui.QSlider(QtCore.Qt.Horizontal, self.groupBox)
        self.manualScaleLwr.move(5,285)
        self.manualScaleLwr.resize(130,25)
        self.manualScaleLwr.setMaximum(100)
        self.manualScaleLwr.setMinimum(0)
        self.manualScaleLwr.setValue(0)
        self.connect(self.manualScaleLwr,QtCore.SIGNAL('valueChanged(int)'),
                     self.manualScaleLwrChanged)
        self.manualScaleUpr = QtGui.QSlider(QtCore.Qt.Horizontal, self.groupBox)
        self.manualScaleUpr.move(5,335)
        self.manualScaleUpr.resize(130,25)
        self.manualScaleUpr.setMaximum(100)
        self.manualScaleUpr.setMinimum(0)
        self.manualScaleUpr.setValue(100)
        self.connect(self.manualScaleUpr,QtCore.SIGNAL('valueChanged(int)'),
                     self.manualScaleUprChanged)

        self.autoscaleLwr = [10,5,2,1,0,0]
        self.autoscaleUpr = [90,95,98,99,100,100]

        self.imageCtr = (-1,-1)
        
        self.showCrosshairs = True
        
        self.fullImage = None
        self.image = None
        self.currentRoi = None

    def manualScaleUprChanged(self, newval):
        self.autoscaleUpr[-1] = newval
        self.update()

    def manualScaleLwrChanged(self, newval):
        self.autoscaleLwr[-1] = newval    
        self.update()

    def setImage(self, image):
        """Set the 2D numpy array of the image"""
        self.fullImage = image
        if self.image is None:
            self.resetFullImage()
        else:
            self.updateRoi()

    def setTitle(self, title):
        """Set the title of the plot"""
        self.title = title

    def setRoi(self, roiStart, roiEnd):
        roi = []
        
        for start,end in zip(roiStart, roiEnd):
            if start < end:
                roi += [int(start), int(end)]
            else:
                roi += [int(end),int(start)]
        self.currentRoi = roi
        self.updateRoi()
        self.update()

    def updateRoi(self):
        try:
            self.image = self.fullImage[int(self.currentRoi[0]):int(self.currentRoi[1]),
                                        int(self.currentRoi[2]):int(self.currentRoi[3])]
        except:
            print "Invalid ROI"
            self.image = self.fullImage

    def resetFullImage(self):
        self.image = self.fullImage
        self.currentRoi = [0,self.image.shape[0],0,self.image.shape[1]]

    def setImageCtr(self,x,y):
        self.imageCtr = [x,y]
        self.update()

    def update(self):
        if self.image is not None:
            self._update()
            
    def _update(self):
        self.axes.clear()

        vmin, vmax = self.autoscaleImage()

        extent = self.currentRoi[0],self.currentRoi[1],self.currentRoi[3],self.currentRoi[2]
        
        self.axes.imshow(self.image, vmin = vmin, 
                         vmax = vmax,
                         extent = extent)
        self.forceAspect()
        if self.title is not None:
            self.axes.set_title(self.title, fontsize = 10)

        cpointx = self.imageCtr[0]
        if (cpointx < 0) or (cpointx >= self.image.shape[0]):
            cpointx = self.image.shape[0] / 2.0
        cpointy = self.imageCtr[1]
        if (cpointy < 0) or (cpointy >= self.image.shape[1]):
            cpointy = self.image.shape[1] / 2.0
            
        lv = self.image[:,int(cpointx)]
        bv = self.image[int(cpointy),:]

        self.axes.xaxis.set_ticklabels([])
        self.axes.yaxis.set_ticklabels([])

        self.axesl.clear()
        self.axesl.plot(lv,range(self.currentRoi[0],self.currentRoi[1]),'r-')
        self.axesl.set_xlim([vmin, vmax])
        self.axesl.set_ylim(self.currentRoi[0:2][::-1])
        self.axesl.xaxis.set_major_locator(MaxNLocator(3))
        
        self.axesb.clear()
        self.axesb.plot(range(self.currentRoi[2],self.currentRoi[3]),bv,'r-')
        self.axesb.set_xlim(self.currentRoi[2:4])
        self.axesb.set_ylim([vmin, vmax])
        self.axesb.yaxis.set_major_locator(MaxNLocator(3))

        if self.showCrosshairs:
            self.axes.axhline(cpointy, linewidth = 1, color = 'k')
            self.axes.axvline(cpointx, linewidth = 1, color = 'k')
            self.axesl.axhline(cpointy, linewidth = 2, color = 'g')
            self.axesb.axvline(cpointx, linewidth = 2, color = 'g')

        self.canvas.draw()

    def motionNotify(self, event):
        #self.imageCtr = event.xdata, event.ydata
        #self.update()
        return

    def autoscaleImage(self):
        for button, lwr, upr in zip(self.autoScaleButtons, self.autoscaleLwr, self.autoscaleUpr):
            if button.isChecked():
                if lwr > upr:
                    vmin, vmax = self._autoscaleImage(lwr = upr, upr = lwr)
                else:
                    vmin, vmax = self._autoscaleImage(lwr = lwr, upr = upr)
                break
        return vmin,vmax
    
    def _autoscaleImage(self, lwr = 10, upr = 90):
        """Return the min and max values"""
        s = numpy.sort(numpy.ravel(self.image))
        pos = int(lwr*len(s)/100.0)
        if pos < 0:
            pos = 0
        l = s[pos]
        pos = int(upr*len(s)/100.0)
        if pos >= len(s):
            pos = -1
        u = s[pos]
            
        return l,u

    def forceAspect(self, aspect = 1.0):
        extent = self.currentRoi
        dataAspect = abs(float(extent[1]-extent[0])/float(extent[3]-extent[2]))/aspect
        if dataAspect:
            self.axes.set_aspect(dataAspect)
