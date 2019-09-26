from PyQt4 import QtCore, QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from ximea import xiapi

from time import sleep

class Parameters(QtGui.QWidget):
	def __init_(self, Parent=None):
		super(Parameters, self).__init__(Parent)

class AtomButtons(QtGui.QWidget):
	def __init__(self,Parent=None):
		super(AtomButtons,self).__init__(Parent)
		self.setup()

	def setup(self):
		self.atomButtonGroup = QtGui.QButtonGroup(self)

		self.atomK = QtGui.QRadioButton('K',self)
		self.atomK.toggle()
		

		self.atomRb = QtGui.QRadioButton('Rb',self)
		# self.atomRb.clicked.connect(self.updateFigure)

		self.atomButtonGroup.addButton(self.atomK)
		self.atomButtonGroup.addButton(self.atomRb)

		self.layout = QtGui.QGridLayout()
		self.layout.addWidget(self.atomK,0,0,1,1)
		self.layout.addWidget(self.atomRb,0,1,1,1)
		self.setLayout(self.layout)

class ImageWindow(QtGui.QWidget):
	def __init__(self,Parent=None):
		super(ImageWindow,self).__init__(Parent)
		self.setup()

	def setup(self):
		self.figure = Figure()
		self.canvas = FigureCanvas(self.figure)
		self.toolbar = NavigationToolbar(self.canvas,self)

		self.layout = QtGui.QGridLayout()
		self.layout.addWidget(self.toolbar,0,0,1,4)
		self.layout.addWidget(self.canvas,1,0,4,4)
		# self.layout.addWidget(self.toolbar,0,0,1,4)
		# self.layout.addWidget(self.toolbar,0,0,1,4)

		self.setLayout(self.layout)

class acquireThread(QtCore.QThread):
	def __init__(self, cam, parent=None):
		QtCore.QThread.__init__(self,parent)
		
		self.cam = cam
		self.running = False
		
		self.Frames = ['Shadow', 'Bright', 'Dark']
		self.Atoms = ['K','Rb']

		self.nAtoms = len(self.Atoms)
		self.nFrames = len(self.Frames)

		self.clearData()

	def clearData(self):
		from copy import deepcopy
		frameData = {}
		self.data = {}
		for k in self.Frames:
			frameData[k] = []
		for k in self.Atoms:
			self.data[k] = deepcopy(frameData)

	def run(self):
		nF = 0
		self.img = xiapi.Image()
		self.cam.start_acquisition()
		
		
		while self.running:
			try:
				
				self.cam.get_image(self.img,timeout=50)
				# print('Image {} collected'.format(nF))
				self.data[self.Atoms[nF % self.nAtoms]][self.Frames[int(nF/self.nAtoms)]] = self.img.get_image_data_numpy()
				
				# print(self.Atoms[nF % self.nAtoms],[self.Frames[int(nF/self.nAtoms)]])
				nF += 1

				if nF >= self.nAtoms*self.nFrames:
					nF = 0
					self.emit(QtCore.SIGNAL("ass"))



			except Exception as e:
				# print e
				pass

def odCalc(data):
	Atoms = ['K','Rb']
	for k in Atoms: 
		data[k]['OD'] = (data[k]['Shadow']-data[k]['Dark'])/(data[k]['Bright']-data[k]['Dark'])


			
def saveData((path,file),data):
	import os, json
	from copy import deepcopy
	if not os.path.isdir(path):
		os.makedirs(path)

	if path[-1] == '/':
		savepath = path + file
	else:
		savepath = path + '/' + file

	imgSave = deepcopy(data)
	imgSave['K'].pop('OD',None)
	imgSave['Rb'].pop('OD',None)
	for i, ibar in imgSave.items():
		for j, jbar in imgSave[i].items():
			imgSave[i][j] = imgSave[i][j].tolist()


	with open(savepath,'w') as outfile:
		json.dump(imgSave,outfile,separators=(',',':')) 


