from PyQt4 import QtCore, QtGui
from ximea import xiapi
from time import sleep
from datetime import datetime

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from sCamera_helpers import *
import numpy as np

SN = '20851142'
DEFAULTPATH = 'C:/Users/Ye Lab/Desktop/Luigi/sCamera/savefiles/'

### NOTE: @50 us exposure, camera saturates at ~1.5mW/cm^2

SENSORWIDTH = []
SENSORHEIGHT = []

class userInterface(QtGui.QWidget):

	def __init__(self):
		super(userInterface, self).__init__(None)

		self.lastFile = 1

		self.setup()
		self.camInitialize()
		
		self.acq = acquireThread(self.cam)
		self.acq.connect(self.acq, QtCore.SIGNAL("ass"), self.doThat)



		# self.camInitialize()

	def setup(self):

		self.setWindowTitle("Ximea sCamera")
		self.resize(500,600)

		self.parameters = Parameters()
		self.setupParameters()
		self.imageWindow = ImageWindow()

		self.buttonParameters = QtGui.QPushButton('Set Parameters')
		self.buttonParameters.clicked.connect(self.openParameters)
		
		self.buttonAcquire = QtGui.QPushButton('Acquire')
		self.buttonAcquire.clicked.connect(self.acquireSequence)

		self.buttonQuit = QtGui.QPushButton('Exit')
		self.buttonQuit.clicked.connect(self.exitSequence)

		self.atomButtonGroup = AtomButtons(self)
		self.atomButtonGroup.atomK.clicked.connect(self.updateFigure)
		self.atomButtonGroup.atomRb.clicked.connect(self.updateFigure)

		self.frameSelect = QtGui.QComboBox(self)
		self.frameSelect.addItem("OD")
		self.frameSelect.addItem("Shadow")
		self.frameSelect.addItem("Bright")
		self.frameSelect.addItem("Dark")
		self.frameSelect.currentIndexChanged.connect(self.updateFigure)
		
		self.messageLog = QtGui.QTextEdit()
		self.messageLog.setReadOnly(True)

		self.layout = QtGui.QGridLayout()
		self.layout.addWidget(self.buttonParameters,1,0,1,1)
		self.layout.addWidget(self.buttonAcquire,2,0)
		self.layout.addWidget(self.buttonQuit,3,0)
		self.layout.addWidget(self.imageWindow,0,0,1,3)
		self.layout.addWidget(self.messageLog,2,1,2,2)
		self.layout.addWidget(self.atomButtonGroup,1,1,1,1)
		self.layout.addWidget(self.frameSelect,1,2,1,1)
		self.setLayout(self.layout)

	def setupParameters(self):
		self.parameters.setWindowTitle("Ximea sCamera Parameters")
		self.parameters.setFixedSize(320,450)
		
		self.parameters.exposureStatic = QtGui.QLabel('Exposure (us)',self)
		self.parameters.xOffsetStatic = QtGui.QLabel('xOffset (px, inc: 16)',self)
		self.parameters.yOffsetStatic = QtGui.QLabel('yOffset (px, inc: 2)',self)
		self.parameters.frameWidthStatic = QtGui.QLabel('Width (px, inc: 16)',self)
		self.parameters.frameHeightStatic = QtGui.QLabel('Height (px, inc: 2)',self)

		self.parameters.exposureEdit = QtGui.QLineEdit('40',self)
		self.parameters.xOffsetEdit = QtGui.QLineEdit('0',self)
		self.parameters.yOffsetEdit = QtGui.QLineEdit('0',self)
		self.parameters.frameWidthEdit = QtGui.QLineEdit('1280',self)
		self.parameters.frameHeightEdit = QtGui.QLineEdit('1024',self)

		self.parameters.frameLabel = QtGui.QLabel("Image Frame", self)
		self.parameters.frameLabel.setFont(QtGui.QFont("Arial",14,QtGui.QFont.Bold))

		self.parameters.buttonGroup = QtGui.QButtonGroup(self)
		self.parameters.exposureStd = QtGui.QRadioButton('Standard Exposure',self)
		self.parameters.exposureStd.toggle()
		self.parameters.exposureStd.clicked.connect(self.exposureModeStd)

		self.parameters.exposureTrg = QtGui.QRadioButton('Exposure on Trigger',self)
		self.parameters.exposureTrg.clicked.connect(self.exposureModeTrg)

		self.parameters.buttonGroup.addButton(self.parameters.exposureStd)
		self.parameters.buttonGroup.addButton(self.parameters.exposureTrg)
		self.parameters.buttonGroupLabel = QtGui.QLabel('Exposure',self)
		self.parameters.buttonGroupLabel.setFont(QtGui.QFont("Arial",14,QtGui.QFont.Bold))

		self.parameters.downsamplingLabel = QtGui.QLabel('Downsampling',self)
		self.parameters.downsamplingLabel.setFont(QtGui.QFont("Arial",14,QtGui.QFont.Bold))
		self.parameters.downsamplingCheck = QtGui.QCheckBox("2x2 Downsampling",self)
		self.parameters.downsamplingCheck.clicked.connect(self.downsamplingMode)

		self.parameters.updateButton = QtGui.QPushButton('Update Parameters')
		self.parameters.updateButton.clicked.connect(self.updateParameters)

		self.parameters.frameStatic = QtGui.QLabel('Framerate (ms)',self)
		self.parameters.frameEdit = QtGui.QLineEdit(self)
		self.parameters.frameEdit.setReadOnly(True)


		self.parameters.savingLabel = QtGui.QLabel('Image saving',self)
		self.parameters.savingLabel.setFont(QtGui.QFont("Arial",14,QtGui.QFont.Bold))

		self.parameters.saveBox = QtGui.QCheckBox('Save Data?',self)
		self.parameters.saveBox.setChecked(True)

		self.parameters.pathLabel = QtGui.QLabel('Path:', self)
		self.parameters.pathEdit = QtGui.QLineEdit(DEFAULTPATH, self)

		self.parameters.fileLabel = QtGui.QLabel('File number:', self)
		self.parameters.fileEdit = QtGui.QLineEdit('{:03d}'.format(self.lastFile), self)
		self.parameters.fileEdit.editingFinished.connect(self.boxChange)



		self.parameters.layout = QtGui.QGridLayout()
		self.parameters.layout.addWidget(self.parameters.frameLabel,0,0,1,2)
		self.parameters.layout.addWidget(self.parameters.exposureStatic,7,0)
		self.parameters.layout.addWidget(self.parameters.exposureEdit,7,1)
		self.parameters.layout.addWidget(self.parameters.xOffsetStatic,1,0)
		self.parameters.layout.addWidget(self.parameters.xOffsetEdit,1,1)
		self.parameters.layout.addWidget(self.parameters.yOffsetStatic,2,0)
		self.parameters.layout.addWidget(self.parameters.yOffsetEdit,2,1)
		self.parameters.layout.addWidget(self.parameters.frameWidthStatic,3,0)
		self.parameters.layout.addWidget(self.parameters.frameWidthEdit,3,1)
		self.parameters.layout.addWidget(self.parameters.frameHeightStatic,4,0)
		self.parameters.layout.addWidget(self.parameters.frameHeightEdit,4,1)

		self.parameters.layout.addWidget(self.parameters.buttonGroupLabel,5,0,1,2)
		self.parameters.layout.addWidget(self.parameters.exposureStd,6,0)
		self.parameters.layout.addWidget(self.parameters.exposureTrg,6,1)

		self.parameters.layout.addWidget(self.parameters.downsamplingLabel,8,0)
		self.parameters.layout.addWidget(self.parameters.downsamplingCheck,9,0)

		self.parameters.layout.addWidget(self.parameters.updateButton,10,0,1,2)

		self.parameters.layout.addWidget(self.parameters.frameStatic,11,0,1,1)
		self.parameters.layout.addWidget(self.parameters.frameEdit,11,1,1,1)

		self.parameters.layout.addWidget(self.parameters.savingLabel,12,0)
		self.parameters.layout.addWidget(self.parameters.saveBox,13,0)
		self.parameters.layout.addWidget(self.parameters.fileLabel,14,0)
		self.parameters.layout.addWidget(self.parameters.fileEdit,14,1)
		self.parameters.layout.addWidget(self.parameters.pathLabel,15,0)
		self.parameters.layout.addWidget(self.parameters.pathEdit,16,0,1,2)

		self.parameters.setLayout(self.parameters.layout)

	def camInitialize(self):
		self.cam = xiapi.Camera()
		self.appendToStatus('Opening Camera with SN: {}...'.format(SN))
		self.cam.open_device_by_SN(SN)
		self.appendToStatus('Camera Model {0} Opened!'.format(self.cam.get_param('device_name')))
		
		global SENSORWIDTH
		global SENSORHEIGHT

		SENSORWIDTH = self.cam.get_param('width:max')
		SENSORHEIGHT = self.cam.get_param('height:max')

		self.parameters.frameEdit.setText('{:.2f}'.format(1000.0/self.cam.get_param('framerate')))


		self.appendToStatus('Sensor {0} x {1} pixels.'.format(SENSORWIDTH,SENSORHEIGHT))

		### SET TRIGGER PROPERTIES
		self.cam.set_param('gpi_mode', 'XI_GPI_TRIGGER')
		self.cam.set_param('trigger_source', 'XI_TRG_EDGE_RISING')
		self.cam.set_param('trigger_selector', 'XI_TRG_SEL_FRAME_START')

		
		# self.cam.set_param('image_data_bit_depth','XI_BPP_10')
		# print(self.cam.get_param('output_bit_depth'))
		# print(self.cam.get_param('sensor_bit_depth'))
		# print(self.cam.get_param('image_data_bit_depth'))

	def updateParameters(self):
		error = False
		try:
			exp = int(float(self.parameters.exposureEdit.text()))	
		except:
			error = True
			self.appendToStatus('Exposure must be a number! Parameters not updated.')
		
		try:
			xoff = int(float(self.parameters.xOffsetEdit.text())/16.0)*16			
		except:
			error = True
			self.appendToStatus('xOffset must be a number! Parameters not updated.')

		try:
			yoff = int(float(self.parameters.yOffsetEdit.text())/2.0)*2			
		except:
			error = True
			self.appendToStatus('yOffset must be a number! Parameters not updated.')

		try:
			fw = int(float(self.parameters.frameWidthEdit.text())/16.0)*16			
		except:
			error = True
			self.appendToStatus('Frame width must be a number! Parameters not updated.')

		try:
			fh = int(float(self.parameters.frameHeightEdit.text())/2.0)*2			
		except:
			error = True
			self.appendToStatus('Frame height must be a number! Parameters not updated.')

		if xoff + fw > SENSORWIDTH/(self.parameters.downsamplingCheck.isChecked() + 1):
			self.appendToStatus('The sum of the xOffset and Width must be less than {}. Parameters not updated.'.format(SENSORWIDTH/(self.parameters.downsamplingCheck.isChecked() + 1)))
			error = True

		if yoff + fh > SENSORHEIGHT/(self.parameters.downsamplingCheck.isChecked() + 1):
			self.appendToStatus('The sum of the yOffset and Height must be less than {}. Parameters not updated.'.format(SENSORHEIGHT/(self.parameters.downsamplingCheck.isChecked() + 1)))
			error = True

		if not error:
			self.parameters.exposureEdit.setText(str(exp))
			self.parameters.frameWidthEdit.setText(str(fw))
			self.parameters.frameHeightEdit.setText(str(fh))
			self.parameters.xOffsetEdit.setText(str(xoff))
			self.parameters.yOffsetEdit.setText(str(yoff))

			self.cam.set_param('exposure',exp)
			self.cam.set_param('width',fw)
			self.cam.set_param('height',fh)
			self.cam.set_param('offsetX',xoff)
			self.cam.set_param('offsetY',yoff)
			self.appendToStatus('Camera parameters successfully updated.')
			self.parameters.frameEdit.setText('{:.2f}'.format(1000.0/self.cam.get_param('framerate')))

	def boxChange(self):
		try:
			x = int(self.parameters.fileEdit.text())
			self.lastfile = x
			self.parameters.fileEdit.setText('{:03d}'.format(x))
		except:
			self.appendToStatus('File number must be an integer.')
			self.parameters.fileEdit.setText('{:03d}'.format(self.lastFile+1))


	def exposureModeStd(self):
		self.cam.set_param('trigger_selector', 'XI_TRG_SEL_FRAME_START')
		self.parameters.exposureEdit.setDisabled(False)

	def exposureModeTrg(self):
		self.cam.set_param('trigger_selector', 'XI_TRG_SEL_EXPOSURE_ACTIVE')
		self.parameters.exposureEdit.setDisabled(True)

	def downsamplingMode(self):
		if self.parameters.downsamplingCheck.isChecked():
			self.cam.set_param('downsampling','XI_DWN_2x2')
			self.parameters.frameWidthEdit.setText(str(int(self.parameters.frameWidthEdit.text())/2))
			self.parameters.frameHeightEdit.setText(str(int(self.parameters.frameHeightEdit.text())/2))
			self.parameters.xOffsetEdit.setText(str(int(self.parameters.xOffsetEdit.text())/2))
			self.parameters.yOffsetEdit.setText(str(int(self.parameters.yOffsetEdit.text())/2))
		else:
			self.cam.set_param('downsampling','XI_DWN_1x1')
			self.parameters.frameWidthEdit.setText(str(int(self.parameters.frameWidthEdit.text())*2))
			self.parameters.frameHeightEdit.setText(str(int(self.parameters.frameHeightEdit.text())*2))
			self.parameters.xOffsetEdit.setText(str(int(self.parameters.xOffsetEdit.text())*2))
			self.parameters.yOffsetEdit.setText(str(int(self.parameters.yOffsetEdit.text())*2))

	def appendToStatus(self,msg):
		self.messageLog.append(msg)
		self.messageLog.moveCursor(QtGui.QTextCursor.End)
		self.messageLog.ensureCursorVisible()
	
	def exitSequence(self):
		self.cam.stop_acquisition()
		self.cam.close_device()
		self.close()
		self.parameters.close()

	def openParameters(self):
		self.parameters.show()

	def acquireSequence(self):
	
		if self.acq.isRunning():
			self.acq.running = False
			self.acq.terminate()
			self.cam.stop_acquisition()

			self.acq.clearData()
			self.appendToStatus('Acquisition Stopped.')
			self.buttonAcquire.setText('Acquire')
		else:
			self.appendToStatus('Starting acqusition.')
			self.buttonAcquire.setText('Stop')
			self.acq.running = True
			self.acq.start()
			


	def doThat(self):

		self.dataHold = self.acq.data
		self.acq.clearData()
		odCalc(self.dataHold)
		self.updateFigure()

		if self.parameters.saveBox.isChecked():
			self.lastFile = int(self.parameters.fileEdit.text())
			self.appendToStatus('Image {:03d} acquired. Saving...'.format(self.lastFile))
			

			path = str(self.parameters.pathEdit.text())
			file = str('XI' + datetime.now().strftime('%Y%m%d') + '_' + self.parameters.fileEdit.text() + '.dat')
			saveData((path,file), self.dataHold)

			self.appendToStatus('Image saved as: ' + file)


			self.parameters.fileEdit.setText('{:03d}'.format(self.lastFile+1))
		else:
			self.appendToStatus('Image acquired.')



	def updateFigure(self):
		frame = str(self.frameSelect.currentText())
		atom = str(self.atomButtonGroup.atomButtonGroup.checkedButton().text())

		def format_coord(x, y):
		    col = int(x + 0.5)
		    row = int(y + 0.5)
		    if col >= 0 and col < numcols and row >= 0 and row < numrows:
		        z = d[row, col]
		        return '({:},{:}), z={:.2f}'.format(int(x),int(y),z)
		    else:
		        return 'x=%1.4f, y=%1.4f' % (x, y)	



		if hasattr(self, 'dataHold'):
			d = self.dataHold[atom][frame]
			numrows, numcols = d.shape
			
			self.imageWindow.figure.clear()
			ax = self.imageWindow.figure.add_subplot(111)
			ax.imshow(d)
			ax.format_coord = format_coord
			self.imageWindow.canvas.draw()



if __name__ == "__main__":
	import sys
	app = QtGui.QApplication(sys.argv)
	ui = userInterface()
	ui.show()
	sys.exit(app.exec_())
	