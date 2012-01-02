# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pyVacuum/ui/graphaxes.ui'
#
# Created: Sun Oct 16 09:43:01 2011
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_AxesDialog(object):
    def setupUi(self, AxesDialog):
        AxesDialog.setObjectName(_fromUtf8("AxesDialog"))
        AxesDialog.resize(525, 380)
        AxesDialog.setMinimumSize(QtCore.QSize(525, 380))
        AxesDialog.setMaximumSize(QtCore.QSize(525, 380))
        self.buttonBox = QtGui.QDialogButtonBox(AxesDialog)
        self.buttonBox.setGeometry(QtCore.QRect(420, 30, 81, 331))
        self.buttonBox.setOrientation(QtCore.Qt.Vertical)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.groupBox = QtGui.QGroupBox(AxesDialog)
        self.groupBox.setGeometry(QtCore.QRect(20, 10, 381, 171))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.LogRadioButton_1 = QtGui.QRadioButton(self.groupBox)
        self.LogRadioButton_1.setGeometry(QtCore.QRect(260, 40, 101, 21))
        self.LogRadioButton_1.setChecked(True)
        self.LogRadioButton_1.setObjectName(_fromUtf8("LogRadioButton_1"))
        self.LinRadioButton_1 = QtGui.QRadioButton(self.groupBox)
        self.LinRadioButton_1.setGeometry(QtCore.QRect(260, 60, 101, 21))
        self.LinRadioButton_1.setObjectName(_fromUtf8("LinRadioButton_1"))
        self.AutoRangeCheckBox_1 = QtGui.QCheckBox(self.groupBox)
        self.AutoRangeCheckBox_1.setGeometry(QtCore.QRect(86, 40, 131, 21))
        self.AutoRangeCheckBox_1.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.AutoRangeCheckBox_1.setChecked(True)
        self.AutoRangeCheckBox_1.setObjectName(_fromUtf8("AutoRangeCheckBox_1"))
        self.MinLineEdit_1 = QtGui.QLineEdit(self.groupBox)
        self.MinLineEdit_1.setEnabled(False)
        self.MinLineEdit_1.setGeometry(QtCore.QRect(82, 100, 141, 22))
        self.MinLineEdit_1.setObjectName(_fromUtf8("MinLineEdit_1"))
        self.MaxLineEdit_1 = QtGui.QLineEdit(self.groupBox)
        self.MaxLineEdit_1.setEnabled(False)
        self.MaxLineEdit_1.setGeometry(QtCore.QRect(82, 70, 141, 22))
        self.MaxLineEdit_1.setObjectName(_fromUtf8("MaxLineEdit_1"))
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setGeometry(QtCore.QRect(20, 100, 61, 17))
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(20, 70, 61, 17))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.groupBox_2 = QtGui.QGroupBox(AxesDialog)
        self.groupBox_2.setGeometry(QtCore.QRect(20, 190, 381, 171))
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.LinRadioButton_2 = QtGui.QRadioButton(self.groupBox_2)
        self.LinRadioButton_2.setGeometry(QtCore.QRect(260, 60, 101, 21))
        self.LinRadioButton_2.setObjectName(_fromUtf8("LinRadioButton_2"))
        self.label_3 = QtGui.QLabel(self.groupBox_2)
        self.label_3.setGeometry(QtCore.QRect(18, 100, 61, 17))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.MinLineEdit_2 = QtGui.QLineEdit(self.groupBox_2)
        self.MinLineEdit_2.setEnabled(False)
        self.MinLineEdit_2.setGeometry(QtCore.QRect(80, 100, 141, 22))
        self.MinLineEdit_2.setObjectName(_fromUtf8("MinLineEdit_2"))
        self.LogRadioButton_2 = QtGui.QRadioButton(self.groupBox_2)
        self.LogRadioButton_2.setGeometry(QtCore.QRect(260, 40, 101, 21))
        self.LogRadioButton_2.setChecked(True)
        self.LogRadioButton_2.setObjectName(_fromUtf8("LogRadioButton_2"))
        self.MaxLineEdit_2 = QtGui.QLineEdit(self.groupBox_2)
        self.MaxLineEdit_2.setEnabled(False)
        self.MaxLineEdit_2.setGeometry(QtCore.QRect(82, 70, 141, 22))
        self.MaxLineEdit_2.setObjectName(_fromUtf8("MaxLineEdit_2"))
        self.AutoRangeCheckBox_2 = QtGui.QCheckBox(self.groupBox_2)
        self.AutoRangeCheckBox_2.setGeometry(QtCore.QRect(80, 40, 141, 21))
        self.AutoRangeCheckBox_2.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.AutoRangeCheckBox_2.setChecked(True)
        self.AutoRangeCheckBox_2.setObjectName(_fromUtf8("AutoRangeCheckBox_2"))
        self.label_4 = QtGui.QLabel(self.groupBox_2)
        self.label_4.setGeometry(QtCore.QRect(20, 70, 61, 17))
        self.label_4.setObjectName(_fromUtf8("label_4"))

        self.retranslateUi(AxesDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), AxesDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), AxesDialog.reject)
        QtCore.QObject.connect(self.AutoRangeCheckBox_1, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.MaxLineEdit_1.setDisabled)
        QtCore.QObject.connect(self.AutoRangeCheckBox_1, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.MinLineEdit_1.setDisabled)
        QtCore.QObject.connect(self.AutoRangeCheckBox_2, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.MaxLineEdit_2.setDisabled)
        QtCore.QObject.connect(self.AutoRangeCheckBox_2, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.MinLineEdit_2.setDisabled)
        QtCore.QMetaObject.connectSlotsByName(AxesDialog)

    def retranslateUi(self, AxesDialog):
        AxesDialog.setWindowTitle(QtGui.QApplication.translate("AxesDialog", "Set Axes Properties", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("AxesDialog", "Y1 AXIS", None, QtGui.QApplication.UnicodeUTF8))
        self.LogRadioButton_1.setText(QtGui.QApplication.translate("AxesDialog", "Log", None, QtGui.QApplication.UnicodeUTF8))
        self.LinRadioButton_1.setText(QtGui.QApplication.translate("AxesDialog", "Linear", None, QtGui.QApplication.UnicodeUTF8))
        self.AutoRangeCheckBox_1.setText(QtGui.QApplication.translate("AxesDialog", "Autorange", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("AxesDialog", "Min", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("AxesDialog", "Max", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("AxesDialog", "Y2 AXIS", None, QtGui.QApplication.UnicodeUTF8))
        self.LinRadioButton_2.setText(QtGui.QApplication.translate("AxesDialog", "Linear", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("AxesDialog", "Min", None, QtGui.QApplication.UnicodeUTF8))
        self.LogRadioButton_2.setText(QtGui.QApplication.translate("AxesDialog", "Log", None, QtGui.QApplication.UnicodeUTF8))
        self.AutoRangeCheckBox_2.setText(QtGui.QApplication.translate("AxesDialog", "Autorange", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("AxesDialog", "Max", None, QtGui.QApplication.UnicodeUTF8))

