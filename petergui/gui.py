from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import os
import sys
import time
import socket
import struct
#from PIL import Image

# This thread reads the image from the robot's camera
class Thread(QThread):
	sig = pyqtSignal()
	server_socket = None
	def __init__(self, address, port, location, parent=None):
		super(QThread, self).__init__()
		self.image_loc = location
		self.server_socket = socket.socket()
		self.server_socket.bind((address,port))
		self.server_socket.listen(0)
		
	def run(self):
		connection = self.server_socket.accept()[0].makefile('rb')
		print("Thread Started")
		try:
			self.running = True
			while self.running:
				image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
				# if the image length is 0 quit the loop and stop the thread
				if not image_len:
					self.running = False
					break
				# construct a stream to hold the image data and read the image
				image_stream = io.BytesIO()
				image_stream.write(connection.read(image_len))
				image_stream.seek(0)
				
				with open(self.image_loc, 'wb') as out:
					out.write(image_stream.read())

				#image = Image.open(image_stream)
				self.sig.emit() # emit a signal to tell the gui its time to update the lable image

		finally:
			connection.close()
			server_socket.close()
				
# Main application GUI
class MainWindow(QWidget):

	def __init__(self, *args, **kwargs):
		QWidget.__init__(self, *args, **kwargs)
		location_r1 = 'image_r1.jpg'
		location_r2 = 'image_r2.jpg'

		self.video_label_r1 = QLabel('Robot 1 Video Feed Unavailable', self)
		self.video_label_r2 = QLabel('Robot 2 Video Feed Unavailable', self)
		self.robot_label_r1 = QLabel("Robot 1",self)
		self.robot_label_r2 = QLabel("Robot 2",self)
		self.slow_stop_button_r1 = QPushButton('Robot1 STOP/SLOW', self)
		self.slow_stop_button_r1.clicked.connect(self.handleButton)
		self.slow_stop_button_r2 = QPushButton('Robot2 2STOP/SLOW', self)
		self.slow_stop_button_r2.clicked.connect(self.handleButton)
		
		#SETTING POSITION
		#horizontal,vertical, size_horizontal, size_vertical
		self.robot_label_r1.setGeometry(10,10,480,30)
		self.robot_label_r2.setGeometry(720,10,480,30)
		self.video_label_r1.setGeometry(10,50,640,480)
		self.video_label_r2.setGeometry(720,50,640,480)
		self.slow_stop_button_r1.setGeometry(10,550,640,100)
		self.slow_stop_button_r2.setGeometry(720,550,640,100)
		
		self.video_reader_r1 = Thread('192.168.0.188', 8000, location_r1)  # Colin edit address
		self.video_reader_r2 = Thread('192.168.0.188', 8001, location_r2)  # Colin edit address
		self.video_reader_r1.start()
		self.video_reader_r2.start()
		self.video_reader_r1.sig.connect(self.on_change_r1)
		self.video_reader_r2.sig.connect(self.on_change_r2)
		self.show()

	def on_change_r1(self, location):
		self.video_label_r1.setPixmap(QPixmap(location))

	def on_change_r2(self, location):
		self.video_label_r2.setPixmap(QPixmap(location))

	def handleButton(self):
		print ('Hello World')

if __name__ == '__main__':

	app = QApplication(sys.argv)
	window = MainWindow()
	window.setFixedSize(1400,800)
	sys.exit(app.exec_())
