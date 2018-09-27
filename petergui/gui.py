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
socket.bind("tcp://*:5555")


# This thread reads the image from the robot's camera
class Thread(QThread):
	sig1 = pyqtSignal()

	def __init__(self, parent=None):
		super(QThread, self).__init__()

	def run(self):
		self.running = True

		while self.running:
			image = socket.recv()
			f = open("image.jpg", 'wb')
			ba = bytearray(base64.b64decode(image))
			#print(ba)
			f.write(ba)
			f.close()
			print("received")
			self.sig1.emit()
			socket.send_string('')  # sends back an empty string
			#time.sleep(1)

			
class MainWindow(QWidget):

	def __init__(self, *args, **kwargs):
		QWidget.__init__(self, *args, **kwargs)

		self.label = QLabel('', self)
		self.layout = QGridLayout()
		self.layout.addWidget(self.label, 0, 0)
		self.setLayout(self.layout)
		self.th = Thread(self)
		self.th.start()
		self.th.sig1.connect(self.on_change)
		self.show()

	def on_change(self):
		self.my_image = QPixmap('image.jpg')
		self.label.setPixmap(self.my_image)


if __name__ == '__main__':

	app = QApplication(sys.argv)
	window = MainWindow()
	sys.exit(app.exec_())


