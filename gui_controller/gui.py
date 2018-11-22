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
import queue
import robotcommands

# CONSTANTS
VIDEO_WIDTH		= 640
VIDEO_HEIGHT		= 480

R1_VIDEO_PORT		= 8000
R1_COMMAND_PORT		= 8001
R1_COUNT_PORT		= 8002

R2_VIDEO_PORT		= 8003
R2_COMMAND_PORT		= 8004
R2_COUNT_PORT		= 8005

#SERVER_ADDRESS		= "192.168.0.188"

# ROBOT		
		

# Sends commands to the robot
class RobotCommandWorker(QThread):
	sig = pyqtSignal(str)
	command_queue = queue.Queue()  # need some kind of queue. can this one work? https://docs.python.org/3/library/queue.html
	
	def __init__(self, context, address, port, robot_name, parent=None):
		super(QThread, self).__init__()
		self.car_count = 0
		self.robot_name = robot_name
		
		# setup command socket
		self.command_socket = context.socket(zmq.REP)
		self.command_socket.bind("tcp://" + str(address) + ':' + str(port))
		
	# when the robot needs to perform a command. add that command to the queue
	def add_command(self, command):
		print("RobotCommandWorker " + self.robot_name + " added command: " + command)
		self.command_queue.put(command)
		print(self.command_queue.qsize())
				
	def run(self):
		print(self.robot_name + ' RobotCommandWorker started')
		try:
			self.command_socket.recv().decode('utf-8') 
			self.running = True
			while self.running:
				
				if self.command_queue.qsize() > 0:
					command = self.command_queue.get()
					print("RobotCommandWorker " + self.robot_name + " command sent: " + command)
					self.command_socket.send_string(command)
					message = self.command_socket.recv().decode('utf-8')
					print("RobotCommandWorker " + self.robot_name + " message received: " + message)
				
				time.sleep(0.1)
					
		finally:
			print(self.robot_name + 'RobotCommandWorker done')

# The RobotStatusWorker is a thread that updates the cars passed label of the robot with the
# current number of cars that have travelled passed the robot.  It also gets the emergency
# vehicle approaching flag from the robot.
class RobotStatusWorker(QThread):
	sig = pyqtSignal(str,str)

	def __init__(self, context, address, port, robot_name, parent=None):
		super(QThread, self).__init__()
		self.robot_name = robot_name
		self.subscriber = context.socket(zmq.SUB)
		self.subscriber.bind("tcp://" + str(address) + ":" + str(port))
		self.subscriber.setsockopt(zmq.SUBSCRIBE, self.robot_name.encode('utf-8')) #subscribes to a specific robot
	
	def run(self):
		print(self.robot_name + ' Car Counting Thread Started')
		try:
			self.running = True
			while self.running:
				[robot_publisher,car_count, emergency_flag] = self.subscriber.recv_multipart()
				car_count = car_count.decode('utf-8')
				emergency_flag = emergency_flag.decode('utf-8')
				
				#print("Recieved %s cars from Robot %s" % robot_publisher,str(car_count))
				self.sig.emit(str(car_count), str(emergency_flag))			
				time.sleep(1)
		finally:
			print(self.robot_name + 'Car Thread done')

# The FrameReaderWorker is a thread that reads video frames from the 
# robot
class FrameReaderWorker(QThread):
	sig = pyqtSignal()

	def __init__(self, address, port, video_frame_file):
		super(QThread, self).__init__()
		self.image_loc =  video_frame_file
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
	def __init__(self, robot_name, context, ip_find_port, server_address, video_port, command_port, count_port):
		QWidget.__init__(self)
		self.robot_name = robot_name
		self.server_address = server_address
		self.video_port = video_port
		self.command_port = command_port
		self.count_port = count_port
		self.emergency_vehicle = True
		self.sign_slow = False
		self.video_frame_file = robot_name + '_video.jpg'
		self.context = context

		# load graphics for sign_pos_label
		self.stop_pic = QPixmap('Stop.png')
		# TODO resize pic so we don't need to scale it
		self.stop_pic = self.stop_pic.scaled(50,50,Qt.KeepAspectRatioByExpanding, Qt.FastTransformation) 
		self.slow_pic = QPixmap('Slow.jpg')
		# TODO resize pic so we don't need to scale it
		self.slow_pic = self.slow_pic.scaled(50,50,Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
		self.create_widget()

		#IP 
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print(robot_name + "starting up on" + server_address)
		sock.bind((server_address, ip_find_port))
		sock.listen(0)
		print("listening")
		connection, client_address = sock.accept()
		#print ('connection from', client_address)

		try:
			# show who connected to us
			print ('connection from', client_address)
		finally:
			print("connection closed")
			connection.close()
			
		
		sock.close()
		print("socket closed")



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
		self.car_count_label = QLabel('0')
		self.robot_status_worker = RobotStatusWorker(self.context, self.server_address, self.count_port, self.robot_name)
		self.robot_status_worker.start()
		self.robot_status_worker.sig.connect(self.on_update_status)
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
		self.robot_command_worker =	RobotCommandWorker(self.context, self.server_address, self.command_port, self.robot_name)
		self.robot_command_worker.start()
		layout.addWidget(self.slow_stop_button)

		# signboard messages
		layout.addWidget(QLabel('Display Message'))
		self.cbox = QComboBox()
		self.cbox.addItem('Stop!')
		self.cbox.addItem('Proceed Slowly')
		self.cbox.addItem('Emergency vehicles only')
		self.cbox.addItem('Stop! There is a problem, please be patient')
		layout.addWidget(self.cbox)
		self.cbox.activated.connect(self.switch_signboard)

		#Button for Resetting Emergency
		self.reset_emergency_button = QPushButton(self.robot_name + 'Reset Emergency Flag')
		layout.addWidget(self.reset_emergency_button)
		self.reset_emergency_button.clicked.connect(self.on_emergency_not_approach)
		self.reset_emergency_button.clicked.connect(self.reset_emergency_flag)

	def on_update_status(self, car_count, emergency_flag):
		print('car count updated')
		self.car_count_label.setText(str(car_count))
		if (emergency_flag == '1'): #True
			self.on_emergency_approach()
		else: #False
			self.on_emergency_not_approach()

	def on_updated_frame(self):
		self.video_label.setPixmap(QPixmap(self.video_frame_file))
	def on_emergency_approach(self):
		#TODO just to test the function and change the color when emergency vehicle is approaching
		           #need to be adjusted
		self.emergency_desc_label.setStyleSheet('color: red')
		self.emergency_ans_label.setStyleSheet('color: red')
		self.emergency_ans_label.setText("Aproaching")
	
	def on_emergency_not_approach(self):
		self.emergency_desc_label.setStyleSheet('color: black')
		self.emergency_ans_label.setStyleSheet('color: black')
		self.emergency_ans_label.setText("None")

	# tells the robot to switch its sign from slow or stop
	def switch_sign(self):
		if (self.sign_slow == True):
			print ("Controller sent STOP signal")
			self.robot_command_worker.add_command(robotcommands.CMD_ROBOT_STOP)
			self.robot_command_worker.add_command(robotcommands.CMD_DISPLAY_STOP)
			self.slow_stop_button.setText("Robot1: Swap to SLOW")
			self.slow_stop_button.setStyleSheet("color: orange")
			self.sign_pos_label.setPixmap(self.stop_pic)
			self.cbox.setCurrentIndex(0)
			self.sign_slow = False
		else:
			print ("Controller sent SLOW signal")
			self.robot_command_worker.add_command(robotcommands.CMD_ROBOT_SLOW)
			self.robot_command_worker.add_command(robotcommands.CMD_ROBOT_RESET_COUNT)
			self.robot_command_worker.add_command(robotcommands.CMD_DISPLAY_PROCEED)
			self.slow_stop_button.setText("Robot1: Swap to STOP")
			self.slow_stop_button.setCheckable(True)
			self.slow_stop_button.setStyleSheet("color: red")
			self.sign_pos_label.setPixmap(self.slow_pic)
			self.cbox.setCurrentIndex(1)
			self.sign_slow = True
			
	def switch_signboard(self,index):
		if (index == 0):
			print ("Signboard will display STOP")
			self.robot_command_worker.add_command(robotcommands.CMD_DISPLAY_STOP)
		elif (index == 1):
			print ("Signboard will display Proceed")
			self.robot_command_worker.add_command(robotcommands.CMD_DISPLAY_PROCEED)
		elif (index == 2):
			print ("Signboard will display Emergency Vehicles only")
			self.robot_command_worker.add_command(robotcommands.CMD_DISPLAY_EMERGENCY)
		elif (index == 3):
			print ("Signboard will display A Problem Has Occured")
			self.robot_command_worker.add_command(robotcommands.CMD_DISPLAY_PROBLEM)
		else:
			print ("Received unknown signboard command")
		
	def reset_emergency_flag(self):
		self.robot_command_worker.add_command(robotcommands.CMD_RESET_EMERGENCY)

# Main application GUI
class MainWindow(QWidget):

	def __init__(self):
		QWidget.__init__(self)

		# get my ip stuff here
		hostname = socket.gethostname()
		server_address = socket.gethostbyname(hostname)
		print("Controller IP Address Found:" + server_address)
		
		# create TCP/IP socket
		context = zmq.Context()

		r1 = RobotControl('Robot1', context, 8007, server_address, R1_VIDEO_PORT, R1_COMMAND_PORT, R1_COUNT_PORT)
		#r2 = RobotControl('Robot2', context, 8006, server_address, R2_VIDEO_PORT, R2_COMMAND_PORT, R2_COUNT_PORT)

		layout = QHBoxLayout(self)
		layout.addWidget(r1)
		#layout.addWidget(r2)

		self.show()
		

#Main 
if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = MainWindow()
	sys.exit(app.exec_())
