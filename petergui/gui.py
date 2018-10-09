from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import os
import sys
import time
import zmq
import base64
#import cv2

context = zmq.Context()
socket = context.socket(zmq.REP)  # using rep and req model. We can improve this
socket2 = context.socket(zmq.REP)

# This thread reads the image from the robot's camera
class Thread(QThread):
	sig1 = pyqtSignal()
	socket.bind("tcp://207.23.201.138:8000")
	def __init__(self, parent=None):
		super(QThread, self).__init__()
		

	def run(self):
		self.running = True
		
		
		while self.running:
			image = socket.recv()
			socket.send_string('')  # sends back an empty string
			f = open("image.jpg", 'wb')
			ba = bytearray(base64.b64decode(image))
			#print(ba)
			f.write(ba)
			f.close()
			print("received image 1")
			self.sig1.emit()
			#time.sleep(1)

class Thread1(QThread):
	sig2 = pyqtSignal()
	socket2.bind("tcp://207.23.201.138:8001")
	def __init__(self, parent=None):
		super(QThread, self).__init__()

	def run(self):
		self.running = True

		while self.running:
			image = socket2.recv()
			socket2.send_string('')
			f = open("image2.jpg", "wb")
			ba = bytearray(base64.b64decode(image))
			f.write(ba)
			f.close()
			print("received image 2")
			self.sig2.emit()
			
class MainWindow(QWidget):

	def __init__(self, *args, **kwargs):
		QWidget.__init__(self, *args, **kwargs)
		self.label = QLabel('', self)
		self.layout = QGridLayout()
		self.label2 = QLabel('', self)
		self.robotlabel1 = QLabel('',self)
		self.robotlabel2 = QLabel('',self)
		self.button = QPushButton('STOP/SLOW', self)
		self.button.clicked.connect(self.handleButton)
		self.button2 = QPushButton('STOP/SLOW', self)
		self.button2.clicked.connect(self.handleButton)
		#horizontalLayout = QHBoxLayout()
		#horizontalLayout.addWidget( self.label )
		#SETTING POSITION
		#horizontal,vertical, size_horizontal, size_vertical
		self.robotlabel1.setGeometry(10,10,480,30)
		self.robotlabel2.setGeometry(720,10,480,30)
		self.label.setGeometry(10,50,640,480)
		self.label2.setGeometry(720,50,640,480)
		self.button.setGeometry(10,550,640,100)
		self.button2.setGeometry(720,550,640,100)
		

		self.robotlabel1.setText("Robot 1")
		self.robotlabel2.setText("Robot 2")
		#self.layout.addWidget(self.label, 0, 0)
		self.setLayout(self.layout)
		self.th = Thread(self)
		self.th1 = Thread1(self)
		self.th.start()
		self.th1.start()
		self.th.sig1.connect(self.on_change)
		self.th1.sig2.connect(self.on_change1)
		self.show()

	def on_change(self):
		self.my_image = QPixmap('image.jpg')
		self.label.setPixmap(self.my_image)
		#self.label2.setPixmap(self.my_image)

	def on_change1(self):
		self.my_image2 = QPixmap('image2.jpg')
		self.label2.setPixmap(self.my_image2)

	def handleButton(self):
		print ('Hello World')

if __name__ == '__main__':

	app = QApplication(sys.argv)
	window = MainWindow()
	window.setFixedSize(1400,800)
	sys.exit(app.exec_())


