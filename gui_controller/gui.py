from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import os
import sys
import time
import socket
import struct
import io
import zmq
import time

#from PIL import Image

context = zmq.Context()
s = context.socket(zmq.REP)
serverAddress = ("207.23.201.64") ##Edit Here = IP 
s.bind("tcp://"+serverAddress+":8002")

#Global Variable
carCount1 = 0

#This thread gets the car count from the robot
class CarCountThread(QThread):
	#sig = pyqtSignal()
	sig = pyqtSignal(str)
	server_socket = None
	def _init_(self, address, port, location, parent=None):
		super(QThread, self).__init__()
	
	def run(self):
		#connection = self.server_socket.accept()[0].makefile('rb')
		print("Car Counting Thread Started")
		try:
			self.running = True
			while self.running:
				carCount1 = s.recv().decode('utf-8')
				#Colin needs to send empty string when he starts the program
				##So this is to ignore that empty string 
				if carCount1 == "":
					print("ignore")
				else:
					self.sig.emit(carCount1)
					
				time.sleep(0.5)
				s.send(b"7")

		finally:
			print("Car Thread done")

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
				
				#with open(self.image_loc, 'wb') as out:
				#	out.write(image_stream.read())
				out = open(self.image_loc,'wb')
				out.write(image_stream.read())
				out.close()
				#image = Image.open(image_stream)
				self.sig.emit() # emit a signal to tell the gui its time to update the lable image

		finally:
			connection.close()
			self.server_socket.close()
			
# Main application GUI
class MainWindow(QWidget):

	def __init__(self, *args, **kwargs):
		QWidget.__init__(self, *args, **kwargs)
		self.set_slow = False
		self.location_r1 = 'image_r1.jpg'
		self.location_r2 = 'image_r2.jpg'

		self.video_label_r1 = QLabel('Robot 1 Video Feed Unavailable', self)
		self.video_label_r2 = QLabel('Robot 2 Video Feed Unavailable', self)
		self.robot_label_r1 = QLabel("Robot 1",self)
		self.robot_label_r2 = QLabel("Robot 2",self)
		self.slow_stop_button_r1 = QPushButton('Robot1 STOP/SLOW', self)
		self.slow_stop_button_r1.clicked.connect(self.handleButton)
		self.slow_stop_button_r2 = QPushButton('Robot2 2STOP/SLOW', self)
		self.slow_stop_button_r2.clicked.connect(self.handleButton)


		#*************************************added**************************************
		#car counting message
		self.robot_car_number_r1 = QLabel("Cars passed= ", self)
		self.robot_car_number_r2 = QLabel("Cars passed= ", self)
		self.car_number_r1 = QLabel("0",self)
		self.car_number_r2 = QLabel("0",self)
		#disolay menu bar
		self.display_r1 = QLabel("Display message:", self)
		self.display_r2 = QLabel("Display message:", self)
		self.comboBox_r1 = QComboBox(self)
		self.comboBox_r2 = QComboBox(self)
		self.comboBox_r1.addItem("Stop!")
		self.comboBox_r1.addItem("Proceed Slowly")
		self.comboBox_r1.addItem("Emergency vehicles only")
		self.comboBox_r1.addItem("Stop! There is a problem, please be patient")
		self.comboBox_r2.addItem("Stop!")
		self.comboBox_r2.addItem("Proceed Slowly")
		self.comboBox_r2.addItem("Emergency vehicles only")
		self.comboBox_r2.addItem("Stop! There is a problem, please be patient")
		self.comboBox_r1.activated[str].connect(self.styleChoice)
		self.comboBox_r2.activated[str].connect(self.styleChoice)
		#emergency vehicle message
		self.EmergencyApproach_r1 = QLabel("Emergency vehicle approaching?:", self)
		self.EmergencyApproach_r2 = QLabel("Emergency vehicle approaching?:", self)
		self.EmergencyThere_r1 = QLabel("No", self)
		self.EmergencyThere_r2 = QLabel("No", self)
		self.Emergency_vehicle()
		#setting buttons to stop and setting the color to res
		self.slow_stop_button_r1.setStyleSheet("color: red")
		self.slow_stop_button_r2.setStyleSheet("color: red")
		#to distinguish between stop and slow. (stop -> true, slow-> false)
		self.slow_stop_button_r1.setCheckable(True)
		self.slow_stop_button_r1.setCheckable(True)
		#adding stop/slow graphics
		self.Graphic_r1 = QLabel(self)
		self.Graphic_r2 = QLabel(self)
		self.pixmap_r1 = QPixmap('Stop.png')
		self.Graphic_r1.setPixmap(self.pixmap_r1)
		self.smaller_pixmap_r1 = self.pixmap_r1.scaled(50,50,Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
		self.Graphic_r1.setPixmap(self.smaller_pixmap_r1)
		self.pixmap_r2 = QPixmap('Stop.png')
		self.Graphic_r2.setPixmap(self.pixmap_r2)
		self.smaller_pixmap_r2 = self.pixmap_r2.scaled(50, 50, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
		self.Graphic_r2.setPixmap(self.smaller_pixmap_r2)
		# *******************************************************************************

		#SETTING POSITION
		#horizontal,vertical, size_horizontal, size_vertical
		self.robot_label_r1.setGeometry(10,10,480,30)
		self.robot_label_r2.setGeometry(720,10,480,30)
		self.video_label_r1.setGeometry(10,50,640,480)
		self.video_label_r2.setGeometry(720,50,640,480)
		self.slow_stop_button_r1.setGeometry(10,550,640,100)
		self.slow_stop_button_r2.setGeometry(720,550,640,100)

		# *************************************added**************************************
		self.robot_car_number_r1.setGeometry(270, 10, 480, 30)
		self.robot_car_number_r2.setGeometry(970, 10, 480, 30)
		self.car_number_r1.setGeometry(440, 10, 480, 30)
		self.car_number_r2.setGeometry(1150, 10, 480, 30)
		self.display_r1.setGeometry(60, 625, 530, 50)
		self.display_r2.setGeometry(770, 625, 530, 50)
		self.comboBox_r1.setGeometry(60,650,530,50)
		self.comboBox_r2.setGeometry(770,650,530,50)
		self.EmergencyApproach_r1.setGeometry(10, 30, 400, 30)
		self.EmergencyApproach_r2.setGeometry(720, 30, 400, 30)
		self.EmergencyThere_r1.setGeometry(420, 30, 50, 30)
		self.EmergencyThere_r2.setGeometry(1140, 30, 50, 30)
		self.Graphic_r1.setGeometry(130, 10, 50, 30)
		self.Graphic_r2.setGeometry(840, 10, 50, 30)
		# *******************************************************************************

		
		self.video_reader_r1 = Thread(serverAddress, 8000, self.location_r1)  # Linda edit address
		self.video_reader_r2 = Thread(serverAddress, 8001, self.location_r2)  # Linda edit address
		self.video_reader_r1.start()
		self.video_reader_r2.start()
		self.video_reader_r1.sig.connect(self.on_change_r1)
		self.video_reader_r2.sig.connect(self.on_change_r2)
		self.car_count_r1 = CarCountThread()
		self.car_count_r1.start()
		self.car_count_r1.sig.connect(self.CarCounting_Robot1)
		
		self.show()

		#--------------------------------------------------------------------#
		#Sending Character
		
		#--------------------------------------------------------------------#



	def on_change_r1(self):
		self.video_label_r1.setPixmap(QPixmap(self.location_r1))

	def on_change_r2(self):
		self.video_label_r2.setPixmap(QPixmap(self.location_r2))

	def handleButton(self):
		"""if (self.set_slow == False):
			print ("Controller sent STOP signal")
			s.recv()
			s.send(b"6")
			self.set_slow = True
		else:
			print ("Controller sent SLOW signal")
			s.recv()
			s.send(b"5")
			self.set_slow = False"""
		s.recv()
		s.send(b"7")
		print("Sending 7")

		#************************added*********************************
		#need to specify when it is stop and slow
		#robot 1
		#if stop, change to slow
		if self.slow_stop_button_r1.isChecked():
			self.slow_stop_button_r1.setText("Robot2 STOP/SLOW: SLOW")
			self.slow_stop_button_r1.setCheckable(False)
			self.slow_stop_button_r1.setStyleSheet("color: orange")
			# changing graphic accordingly
			self.pixmap_r1 = QPixmap('Slow.jpg')
			self.Graphic_r1.setPixmap(self.pixmap_r1)
			self.smaller_pixmap_r1 = self.pixmap_r1.scaled(50, 50, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
			self.Graphic_r1.setPixmap(self.smaller_pixmap_r1)
			#setting display message
			self.comboBox_r1.setCurrentIndex(1)
			self.styleChoice("Proceed Slowly")
		#if slow change to stop
		else:
			self.slow_stop_button_r1.setText("Robot2 STOP/SLOW: STOP")
			self.slow_stop_button_r1.setCheckable(True)
			self.slow_stop_button_r1.setStyleSheet("color: red")
			# changing graphic accordingly
			self.pixmap_r1 = QPixmap('Stop.png')
			self.Graphic_r1.setPixmap(self.pixmap_r1)
			self.smaller_pixmap_r1 = self.pixmap_r1.scaled(50, 50, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
			self.Graphic_r1.setPixmap(self.smaller_pixmap_r1)
			# setting display message
			self.comboBox_r1.setCurrentIndex(0)
			self.styleChoice("Stop!")
		# robot 2
		# if stop, change to slow
		if self.slow_stop_button_r2.isChecked():
			self.slow_stop_button_r2.setText("Robot2 STOP/SLOW: SLOW")
			self.slow_stop_button_r2.setCheckable(False)
			self.slow_stop_button_r2.setStyleSheet("color: orange")
			#changing graphic accordingly
			self.pixmap_r2 = QPixmap('Slow.jpg')
			self.Graphic_r2.setPixmap(self.pixmap_r2)
			self.smaller_pixmap_r2 = self.pixmap_r2.scaled(50, 50, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
			self.Graphic_r2.setPixmap(self.smaller_pixmap_r2)
			# setting display message
			self.comboBox_r2.setCurrentIndex(1)
			self.styleChoice("Proceed Slowly")
		# if slow change to stop
		else:
			self.slow_stop_button_r2.setText("Robot2 STOP/SLOW: STOP")
			self.slow_stop_button_r2.setCheckable(True)
			self.slow_stop_button_r2.setStyleSheet("color: red")
			# changing graphic accordingly
			self.pixmap_r2 = QPixmap('Stop.png')
			self.Graphic_r2.setPixmap(self.pixmap_r2)
			self.smaller_pixmap_r2 = self.pixmap_r2.scaled(50, 50, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
			self.Graphic_r2.setPixmap(self.smaller_pixmap_r2)
			# setting display message
			self.comboBox_r2.setCurrentIndex(0)
			self.styleChoice("Stop!")
		#*************************************************************


		#commented these to change the colors since I didn't have the clients
		#response = s.recv()
		#print(response)
		#s.send(data.encode('utf-8'))
		#print("Sent the character")





	# *************************************added**************************************
	def CarCounting_Robot1(self, value):
		#not sure if the number of you are reading from sensors is string or integer
		#But assuming it is integer, however, the function needs to be adjusted according to the way
		#data are read
		#this is just for testing the function
		#carNumber1 = 1
		#carNumber2 = 1
		self.car_number_r1.setText(str(value))
		#self.car_number_r2.setText(str(carNumber2))

	def styleChoice(self, text):
		#need to distinguish between robot 1 or 2 -> not yet
		print(text)

	def Emergency_vehicle(self):
		#just to test the function and change the color when emergency vehicle is approaching
		#need to be adjusted
		self.EmergencyApproach_r1.setStyleSheet('color: red')
		self.EmergencyThere_r1.setText("Yes")
		self.EmergencyThere_r1.setStyleSheet('color: red')


# *******************************************************************************


if __name__ == '__main__':

	app = QApplication(sys.argv)
	window = MainWindow()
	window.setFixedSize(1400,800)
	sys.exit(app.exec_())
