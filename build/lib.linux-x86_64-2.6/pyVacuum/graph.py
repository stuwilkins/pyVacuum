#
# pyVacuumGraph.py (c) Stuart B. Wilkins 2008
#
# $Id: graph.py 88 2009-01-07 02:20:19Z swilkins $
# $HeadURL: https://solids.phy.bnl.gov/svn/pyVacuum/pyVacuum/graph.py $
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

import os.path
import time, random, itertools

from PyQt4.Qt import *
import PyQt4.Qwt5 as Qwt
from PyQt4.Qwt5.anynumpy import *

# Get directory of images from module pyVacuum
import pyVacuum
import pyVacuum.config as config

from ui.graphaxes import *

import logging as log
logging = log.getLogger(__name__)

class pyVacGraphAxesDialog(QDialog):
    def __init__(self, *args):
        QDialog.__init__(self, *args)
        self.ui = Ui_AxesDialog()
        self.ui.setupUi(self)

class PlotPicker(Qwt.QwtPlotPicker):
    def __init__(self, *args):
        Qwt.QwtPlotPicker.__init__(self, *args)
    
    def trackerText(self, point):
        
        x = self.plot().invTransform(Qwt.QwtPlot.xBottom, point.x())
        y1 = self.plot().invTransform(Qwt.QwtPlot.yLeft, point.y())
        y2 = self.plot().invTransform(Qwt.QwtPlot.yRight, point.y())
        t = time.strftime("%H:%M:%S", time.localtime(x))

        text = "%s, %4.3e, %4.3e" % (t, y1, y2)
        return Qwt.QwtText(text)

class pyVacGraphWindow(QMainWindow):
    def __init__(self, parent = None, *args):
        QMainWindow.__init__(self, parent, *args)

        # Images are in the modules directory
        imagesdir = os.path.join(pyVacuum.__path__[0], 'images')
        self.graphImage = config.graphImageFilename

        self.statusBar().showMessage("Ready")

        self.setWindowTitle(config.graphWindowTitle)
        self.plot = pyVacGraph(self)
        self.setCentralWidget(self.plot)
        self.plot.setMargin(5)

        self.resize(config.graphWindowSize[0],
                    config.graphWindowSize[1])

        # Set the icon

        self.setWindowIcon(QIcon(os.path.join(imagesdir, 'pyVacuumIcon.jpg')))
        self.setContextMenuPolicy(Qt.NoContextMenu)

        # Setup zoomers and pickers
        
        #self.zoomers = []
        #zoomer = Qwt.QwtPlotZoomer(
        #    Qwt.QwtPlot.xBottom,
        #    Qwt.QwtPlot.yLeft,
        #    Qwt.QwtPicker.DragSelection,
        #    Qwt.QwtPicker.AlwaysOff,
        #    self.plot.canvas())
        #zoomer.setRubberBandPen(QPen(QColor("Red")))
        #self.zoomers.append(zoomer)

        #zoomer = Qwt.QwtPlotZoomer(
        #    Qwt.QwtPlot.xBottom,
        #    Qwt.QwtPlot.yLeft,
        #    Qwt.QwtPicker.PointSelection | Qwt.QwtPicker.DragSelection,
        #    Qwt.QwtPicker.AlwaysOff,
        #    self.plot.canvas())
        #zoomer.setRubberBand(Qwt.QwtPicker.NoRubberBand)
        #self.zoomers.append(zoomer)

        self.picker = PlotPicker(
            Qwt.QwtPlot.xBottom,
            Qwt.QwtPlot.yRight,
            Qwt.QwtPicker.PointSelection | Qwt.QwtPicker.DragSelection,
            Qwt.QwtPlotPicker.CrossRubberBand,
            Qwt.QwtPicker.AlwaysOn,
            self.plot.canvas())
        self.picker.setRubberBandPen(QPen(QColor("Green")))
        self.picker.setTrackerPen(QPen(QColor("Red")))

        # Toolbar

        toolBar = QToolBar(self)
        self.addToolBar(toolBar)
        btnPrint = QToolButton(toolBar)
        btnPrint.setText("Print")
        btnPrint.setIcon(QIcon(os.path.join(imagesdir, "print-128.png")))
        btnPrint.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolBar.addWidget(btnPrint)
        self.connect(btnPrint, SIGNAL('clicked()'), self.print_)

        if QT_VERSION >= 0X040100:
            btnPDF = QToolButton(toolBar)
            btnPDF.setText("PDF")
            btnPDF.setIcon(
                QIcon(os.path.join(imagesdir, "print-128.png")))
            btnPDF.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            toolBar.addWidget(btnPDF)
            self.connect(btnPDF, SIGNAL('clicked()'), self.exportPDF)

        if QT_VERSION >= 0x040300:
            btnSVG = QToolButton(toolBar)
            btnSVG.setText("SVG")
            btnSVG.setIcon(
                QIcon(os.path.join(imagesdir, "print-128.png")))
            btnSVG.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            toolBar.addWidget(btnSVG)            
            self.connect(btnSVG, SIGNAL('clicked()'), self.exportSVG)
            
        toolBar.addSeparator()

        #btnZoom = QToolButton(toolBar)
        #btnZoom.setText("Zoom")
        #btnZoom.setIcon(QIcon("images/zoom-128.png"))
        #btnZoom.setCheckable(True)
        #btnZoom.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        #toolBar.addWidget(btnZoom)
        
        #toolBar.addSeparator()
        btnAxis = QToolButton(toolBar)
        btnAxis.setText("Y Axis")
        btnAxis.setIcon(QIcon(os.path.join(imagesdir, "graph-128.png")))
        btnAxis.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolBar.addWidget(btnAxis)
        #btnY2Axis = QToolButton(toolBar)
        #btnY2Axis.setText("Y2 Axis")
        #btnY2Axis.setIcon(QIcon("images/graph-128.png"))
        #btnY2Axis.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        #toolBar.addWidget(btnY2Axis)

        #self.connect(btnZoom,
        #             SIGNAL('toggled(bool)'),
        #             self.zoomit)
        self.connect(self.picker,
                     SIGNAL('moved(const QPoint &)'),
                     self.moved)
        self.connect(self.picker,
                     SIGNAL('selected(const QaPolygon &)'),
                     self.selected)
        self.connect(btnAxis,
                     SIGNAL('clicked()'),
                     self.plot.showAxisDialog)

    def moved(self, point):
        info = "%s, Y1=%e, Y2=%e" % (
            time.asctime(time.localtime(self.plot.invTransform(Qwt.QwtPlot.xBottom, point.x()))),
            self.plot.invTransform(Qwt.QwtPlot.yLeft, point.y()),
            self.plot.invTransform(Qwt.QwtPlot.yRight, point.y()))
        self.showInfo(info)
        
    def selected(self, _):
        self.showInfo()

    def getPlot(self):
        return self.plot

    #def zoomit(self, on):
    #    for z in self.zoomers:
    #        z.setEnabled(on)
    #        z.zoom(0)
    #    
    #    if on:
    #        self.picker.setRubberBand(Qwt.QwtPicker.NoRubberBand)
    #    else:
    #        self.picker.setRubberBand(Qwt.QwtPicker.CrossRubberBand)
    #
    #    self.showInfo()


    def print_(self):
        printer = QPrinter(QPrinter.HighResolution)

        printer.setOutputFileName('pyVacuum-%s.ps' % qVersion())

        printer.setCreator('pyVacuum')
        printer.setOrientation(QPrinter.Landscape)
        printer.setColorMode(QPrinter.Color)

        docName = self.plot.title().text()
        if not docName.isEmpty():
            docName.replace(QRegExp(QString.fromLatin1('\n')), self.tr(' -- '))
            printer.setDocName(docName)

        dialog = QPrintDialog(printer)
        print dialog.exec_()

        if dialog.exec_():
            filter = PrintFilter()
            if (QPrinter.GrayScale == printer.colorMode()):
                filter.setOptions(
                    QwtPlotPrintFilter.PrintAll
                    & ~QwtPlotPrintFilter.PrintBackground
                    | QwtPlotPrintFilter.PrintFrameWithScales)
            self.plot.print_(printer, filter)

    def exportPDF(self):
        if QT_VERSION > 0x040100:
            fileName = QFileDialog.getSaveFileName(
                self,
                'Export File Name',
                'pyVacuum-%s.pdf' % qVersion(),
                'PDF Documents (*.pdf)')

        if not fileName.isEmpty():
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOrientation(QPrinter.Landscape)
            printer.setOutputFileName(fileName)

            printer.setCreator('pyVacuum')
            self.plot.print_(printer)

    
    def exportSVG(self):
        if QT_VERSION >= 0x040300:
            fileName = QFileDialog.getSaveFileName(
                self,
                'Export File Name',
                'bode-example-%s.svg' % qVersion(),
                'SVG Documents (*.svg)')
            if not fileName.isEmpty():
                generator = QSvgGenerator()
                generator.setFileName(fileName)
                generator.setSize(QSize(800, 600))
                self.plot.print_(generator)

    
    def showInfo(self, text=None):
        if not text:
            if self.picker.rubberBand():
                text = 'Cursor Pos: Press left mouse button in plot region'
            else:
                text = 'Zoom: Press mouse button and drag'
                
        self.statusBar().showMessage(text)
                
    
class pyVacGraph(Qwt.QwtPlot):
    def __init__(self, *args):
        Qwt.QwtPlot.__init__(self, *args)

        self.setCanvasBackground(QColor("LightGrey"))

        self.colors = itertools.cycle([Qt.red, Qt.green, Qt.blue, Qt.cyan,
                                       Qt.magenta, Qt.yellow, Qt.darkRed,
                                       Qt.darkGreen, Qt.darkBlue, Qt.darkCyan,
                                       Qt.darkMagenta, Qt.darkYellow])

        # legend
        
        self.legend = Qwt.QwtLegend()
        self.legend.setItemMode(Qwt.QwtLegend.ClickableItem)
        self.legend.setFrameStyle(QFrame.Box | QFrame.Sunken)
        self.insertLegend(self.legend, Qwt.QwtPlot.RightLegend)

        self.connect(self, SIGNAL("legendClicked(QwtPlotItem *)"),
                     self.legendClicked)
        # Axes

        self.setAxisScaleEngine(Qwt.QwtPlot.yLeft,
                                Qwt.QwtLog10ScaleEngine())
        self.setAxisScaleEngine(Qwt.QwtPlot.yRight,
                                Qwt.QwtLinearScaleEngine())

        self.axisScaleEngine(Qwt.QwtPlot.yLeft).setAttribute(
            Qwt.QwtScaleEngine.Floating)

        self.setAxisTitle(Qwt.QwtPlot.xBottom, "Time [h:m:s]")

        sd = TimeScaleDraw()
        self.setAxisScaleDraw(Qwt.QwtPlot.xBottom, sd)

        self.enableAxis(Qwt.QwtPlot.yRight)

        # Setup list of plots to hold
        
        self.curve = {}

    def plotData(self, key, axis = 0, x = None, y = None):
        """
        plot data (x, y) on the graph axis "axis"
        if axis is zero then remove the plot from the graph
        """

        # First if the plot exists then delete it! 

        if not self.curve.has_key(key) and not axis:
            return True

        if self.curve.has_key(key) and not axis:
            # We are plotting this curve
            self.curve[key].attach(None)
            self.curve.__delitem__(key)
            return True
        
        if not self.curve.has_key(key):
            c = Qwt.QwtPlotCurve(key)
            self.setLineStyle(c)
            self.curve[key] = c

        self.curve[key].setData(x, y)
        
        if axis & 1:
            self.curve[key].setYAxis(Qwt.QwtPlot.yLeft)
        if axis & 2:
            self.curve[key].setYAxis(Qwt.QwtPlot.yRight)

        self.curve[key].attach(self)

        return True

    def showAxisDialog(self):

        # todo : converting to double ... check b

        dialog = pyVacGraphAxesDialog(self)

        if type(self.axisScaleEngine(Qwt.QwtPlot.yLeft)) == type(Qwt.QwtLog10ScaleEngine()):
            dialog.ui.LogRadioButton_1.setChecked(True)
        else:
            dialog.ui.LinRadioButton_1.setChecked(True)

        if type(self.axisScaleEngine(Qwt.QwtPlot.yRight)) == type(Qwt.QwtLog10ScaleEngine()):
            dialog.ui.LogRadioButton_2.setChecked(True)
        else:
            dialog.ui.LinRadioButton_2.setChecked(True)  

        if self.axisAutoScale(Qwt.QwtPlot.yLeft):
            dialog.ui.AutoRangeCheckBox_1.setChecked(True)

        if self.axisAutoScale(Qwt.QwtPlot.yRight):
            dialog.ui.AutoRangeCheckBox_2.setChecked(True)
            


        if dialog.exec_() == QDialog.Accepted:
            # Set the axes
            if dialog.ui.LogRadioButton_1.isChecked():
                self.setAxisScaleEngine(Qwt.QwtPlot.yLeft,
                                        Qwt.QwtLog10ScaleEngine())
            else:
                self.setAxisScaleEngine(Qwt.QwtPlot.yLeft,
                                        Qwt.QwtLinearScaleEngine())
            
            if dialog.ui.LogRadioButton_2.isChecked():
                self.setAxisScaleEngine(Qwt.QwtPlot.yRight,
                                        Qwt.QwtLog10ScaleEngine())
            else:
                self.setAxisScaleEngine(Qwt.QwtPlot.yRight,
                                        Qwt.QwtLinearScaleEngine())

            if dialog.ui.AutoRangeCheckBox_1.isChecked():
                self.setAxisAutoScale(Qwt.QwtPlot.yLeft)
            else:
                min, b = dialog.ui.MinLineEdit_1.text().toDouble()
                max, b = dialog.ui.MaxLineEdit_1.text().toDouble()
                self.setAxisScale(Qwt.QwtPlot.yLeft,min, max)

            if dialog.ui.AutoRangeCheckBox_2.isChecked():
                self.setAxisAutoScale(Qwt.QwtPlot.yRight)
            else:
                min, b = dialog.ui.MinLineEdit_2.text().toDouble()
                max, b = dialog.ui.MaxLineEdit_2.text().toDouble()
                self.setAxisScale(Qwt.QwtPlot.yRight,min, max)

            self.replot()

    def legendClicked(self, item):
        color=QColorDialog.getColor(QColor("Red"), self)
        self.setLineStyle(item, color)

    def setLineStyle(self, item, color = None):
        if color is None:
            color = QColor(self.colors.next())
        item.setPen(QPen(color, 1))
        item.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.Ellipse,
                                     QBrush(color),
                                     QPen(color, 1),
                                     QSize(5, 5)))
        self.replot()

    def dumpWidget(self):

        if self.parentWidget() is not None:
            pixmap = QPixmap.grabWidget(self.parentWidget())
        else:
            pixmap = QPixmap.grabWidget(self)
            
        pixmap.save(self.parentWidget().graphImage)

class TimeScaleDraw(Qwt.QwtScaleDraw):
    def __init__(self):
        Qwt.QwtScaleDraw.__init__(self)
    def label(self, v):
        s = time.strftime("%H:%M:%S", time.localtime(v))
        s = QString(s)
        return Qwt.QwtText(s)

    def font(self, f, _):
        result = QFont(f)
        result.setPointSize(int(f.pointSize()*1.25))
        return result

