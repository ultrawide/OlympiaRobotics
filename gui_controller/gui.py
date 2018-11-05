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

# CONSTANTS
VIDEO_WIDTH		= 640
VIDEO_HEIGHT		= 480

R1_VIDEO_PORT		= 8000
R1_COMMAND_PORT		= 8001
R1_COUNT_PORT		= 8002

R2_VIDEO_PORT		= 8003
R2_COMMAND_PORT		= 8004
R2_COUNT_PORT		= 8005

SERVER_ADDRESS		= "192.168.0.188"


# The CarCountWorker is a thread that updates the cars passed label of the robot with the
# current number of cars that have travelled passed the robot
class CarCountWorker(QThread):
	sig = pyqtSignal(str)

	def __init__(self, address, port, robot_name, parent=None):
		super(QThread, self).__init__()
		self.robot_name = robot_name
		context = zmq.Context()
		self.socket = context.socket(zmq.REP)
		self.socket.bind("tcp://" + str(address) + ":" + str(port))
	
	def run(self):
		print(self.robot_name + ' Car Counting Thread Started')
		try:
			self.running = True
			while self.running:
				car_count = self.socket.recv().decode('utf-8')

				#Colin needs to send empty string when he starts the program
				#So this is to ignore that empty string 
				if car_count != '':
					self.sig.emit(car_count)
					
				time.sleep(0.5)
				s3.send(b"7")

		finally:
			print(self.robot_name + 'Car Thread done')

# The FrameReaderWorker is a thread that reads video frames from the 
# robot
class FrameReaderWorker(QThread):
	sig = pyqtSignal()

	def __init__(self, address, port, location):
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

				self.sig.emit() # emit a signal to tell the gui its time to update the label image
		finally:
			connection.close()
			self.server_socket.close()

# RobotControl is a widget that controls a single robot		
class RobotControl(QWidget):
	def __init__(self, robot_name, server_address, video_port, command_port, count_port):
		QWidget.__init__(self)
		self.robot_name = robot_name
		self.server_address = server_address
		self.video_port = video_port
		self.command_port = command_port
		self.count_port = count_port
		self.car_count = 0
		self.emergency_vehicle = True
		self.sign_slow = False
		self.video_frame_file = robot_name + '_video.png'

		# load graphics for sign_pos_label
		self.stop_pic = QPixmap('Stop.png')
		# TODO resize pic so we don't need to scale it
		self.stop_pic = self.stop_pic.scaled(50,50,Qt.KeepAspectRatioByExpanding, Qt.FastTransformation) 
		self.slow_pic = QPixmap('Slow.jpg')
		# TODO resize pic so we don't need to scale it
		self.slow_pic = self.slow_pic.scaled(50,50,Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)

		self.create_widget()

		# setup command socket
		context = zmq.Context()
		self.command_socket = context.socket(zmq.REP)
		self.command_socket.bind("tcp://" + str(server_address) + ':' + str(command_port))

	def create_widget(self):
		# main layout widget
		layout = QVBoxLayout(self)

		# robot status 'car count, sign position'
		status_layout = QHBoxLayout()
		status_layout.addWidget(QLabel(self.robot_name))
		self.sign_pos_label = QLabel('')
		self.sign_pos_label.setPixmap(self.stop_pic)
		status_layout.addWidget(self.sign_pos_label)
		label = QLabel('Cars passed: ', self)
		label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		status_layout.addWidget(label)
		self.car_count_label = QLabel('0', self)
		self.car_count_reader = CarCountWorker(self.server_address, self.count_port, self.robot_name)
		self.car_count_reader.start()
		self.car_count_reader.sig.connect(self.on_updated_count)
		status_layout.addWidget(self.car_count_label)
		layout.addLayout(status_layout)

		# emergency vehicle status layout
		emergency_layout = QHBoxLayout()
		self.emergency_desc_label = QLabel('Emergency vehicle approaching:')
		emergency_layout.addWidget(self.emergency_desc_label)
		self.emergency_ans_label = QLabel('None',self)
		self.emergency_ans_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
		emergency_layout.addWidget(self.emergency_ans_label)
		layout.addLayout(emergency_layout)
		
		# video feed
		self.video_label = QLabel(self.robot_name + 'Video Feed Unavailable')
		self.video_label.setMinimumSize(VIDEO_WIDTH, VIDEO_HEIGHT)
		self.video_label.setMaximumSize(VIDEO_WIDTH, VIDEO_HEIGHT)
		self.video_reader = FrameReaderWorker(self.server_address, self.video_port, self.video_frame_file)
		self.video_reader.start()
		self.video_reader.sig.connect(self.on_updated_frame)
		layout.addWidget(self.video_label)

		# slow/stop button
		self.slow_stop_button = QPushButton(self.robot_name + ' Slow/Stop Button')
		self.slow_stop_button.clicked.connect(self.switch_sign)
		layout.addWidget(self.slow_stop_button)

		# signboard messages
		layout.addWidget(QLabel('Display Message'))
		self.cbox = QComboBox()
		self.cbox.addItem('Stop!')
		self.cbox.addItem('Proceed Slowly')
		self.cbox.addItem('Emergency vehicles only')
		self.cbox.addItem('Stop! There is a problem, please be patient')
		layout.addWidget(self.cbox)

	def on_updated_count(self, car_count):
		print('car count updated')
		self.car_count_label.setText(str(self.car_count))

	def on_updated_frame(self):
		self.video_label.setPixmap(QPixmap(self.video_frame_file))

	def on_emergency_approach(self):
		#TODO just to test the function and change the color when emergency vehicle is approaching
		           #need to be adjusted
		emergency_desc_label.setStyleSheet('color: red')
		emergency_ans_label.setStyleSheet('color: red')
		emergency_ans_label.setText("Aproaching")
	
	# tells the robot to switch its sign from slow or stop
	def switch_sign(self):
		if (self.sign_slow == False):
			print ("Controller sent STOP signal")
			#self.command_socket.recv()
			#self.command_socket.send(b"6")
			self.sign_slow = True
		else:
			print ("Controller sent SLOW signal")
			#Logic for Resetting Car Count
			#if (self.Robot1CarCount == self.Robot2CarCount and self.set_slow_r1 == False and self.set_slow_r2 == False):
				#count_socket.recv()
				#Sending Reset Command to Raspberry Pi
				#count_socket.send(b"8")

			#self.command_socket.recv()
			#self.command_socket.send(b"5")
			self.sign_slow = False
			#count_socket.recv()
			#count_socket.send(b"8")

		#************************added*********************************
		#need to specify when it is stop and slow
		#robot 1
		#if stop, change to slow
		if self.slow_stop_button.isChecked():
			self.slow_stop_button.setText("Robot1: Swap to SLOW")
			self.slow_stop_button.setCheckable(False)
			self.slow_stop_button.setStyleSheet("color: orange")

			# changing graphic accordingly
			self.sign_pos_label.setPixmap(self.slow_pic)

			# setting display message
			self.cbox.setCurrentIndex(0)

		#if slow change to stop
		else:
			self.slow_stop_button.setText("Robot1: Swap to STOP")
			self.slow_stop_button.setCheckable(True)
			self.slow_stop_button.setStyleSheet("color: red")

			# changing graphic accordingly
			self.sign_pos_label.setPixmap(self.stop_pic)

			#setting display message
			self.cbox.setCurrentIndex(1)
		

# Main application GUI
class MainWindow(QWidget):

	def __init__(self, *args, **kwargs):
		QWidget.__init__(self, *args, **kwargs)

		r1 = RobotControl('Robot 1', SERVER_ADDRESS, R1_VIDEO_PORT, R1_COMMAND_PORT, R1_COUNT_PORT)
		r2 = RobotControl('Robot 2', SERVER_ADDRESS, R2_VIDEO_PORT, R2_COMMAND_PORT, R2_COUNT_PORT)

		layout = QHBoxLayout(self)
		layout.addWidget(r1)
		layout.addWidget(r2)

		self.show()

#Main 
if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = MainWindow()
	sys.exit(app.exec_())
