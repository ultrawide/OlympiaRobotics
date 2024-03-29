from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import fcntl
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
import robo_library
from threading import Thread, Lock

# CONSTANTS
ROBOT1_NAME	= "Robot1"
ROBOT2_NAME = "Robot2"

VIDEO_WIDTH		= 320
VIDEO_HEIGHT		= 240

R1_VIDEO_PORT		= 8000
R1_COMMAND_PORT		= 8001
R1_COUNT_PORT		= 8002

R2_VIDEO_PORT		= 8003
R2_COMMAND_PORT		= 8004
R2_COUNT_PORT		= 8005

IP_LOCATION_PORT	= 8007

NET_ADAPTER = 'wlp2s0'

# added to lock the buttons when one is at slow
ButtonLock = {"button":False, "CarCount":False}

# Sends commands to the robot
class RobotCommandWorker(QThread):
	sig = pyqtSignal(str)
	
	def __init__(self, context, address, port, robot_name, parent=None):
		super(QThread, self).__init__()
		self.command_queue = queue.Queue()
		self.car_count = 0
		self.robot_name = robot_name
		
		# setup command socket
		self.command_socket = context.socket(zmq.REP)
		self.command_socket.bind("tcp://" + str(address) + ':' + str(port))
		#print(self.robot_name + " RobotCommandWorker started")
		
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
	sig = pyqtSignal(str, str,str)

	def __init__(self, context, address, port, robot_name, parent=None):
		super(QThread, self).__init__()
		self.robot_name = robot_name
		self.subscriber = context.socket(zmq.SUB)
		self.subscriber.bind("tcp://" + str(address) + ":" + str(port))
		self.subscriber.setsockopt(zmq.SUBSCRIBE, self.robot_name.encode('utf-8')) #subscribes to a specific robot
	
	def run(self):
		print(self.robot_name + ' Car Counting Thread Started')
		#self.sig.emit(str(self.robot_name), str(0), str(0))
		try:
			self.running = True
			while self.running:
				[robot_publisher,car_count, emergency_flag] = self.subscriber.recv_multipart()
				car_count = car_count.decode('utf-8')
				emergency_flag = emergency_flag.decode('utf-8')
				
				#print("Recieved %s cars from Robot %s" % robot_publisher,str(car_count))
				self.sig.emit(str(self.robot_name), str(car_count), str(emergency_flag))			
				time.sleep(.25)
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


# Thread runs in the background waiting for connection from the robots
class IPLocationWorker(QThread):
	def __init__(self, server_address, ip_find_port):
		super(QThread, self).__init__()
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print("starting ip location service on" + server_address)
		self.sock.bind((server_address, int(ip_find_port)))
		self.sock.listen(1)
		
	def run(self):
		print("listening for connection from robots")
		count = 0
		while count < 2:
			connection, client_address = self.sock.accept()
			try:
				print ('connection from', client_address)
				count += count + 1
			finally:
				print("connection closed")
				connection.close()

		self.sock.close()
		print("socket closed")


# RobotControl is a widget that controls a single robot		
class RobotControl(QWidget):
	def __init__(self, robot_name, context, server_address, video_port, command_port, count_port):
		QWidget.__init__(self)
		self.robot_name = robot_name
		self.server_address = server_address
		self.video_port = video_port
		self.command_port = command_port
		self.count_port = count_port
		self.emergency_vehicle = True
		self.sign_slow = False
		self.video_frame_file = robot_name + '_video.jpg'
		self.count_port = count_port
		self.context = context

		#added for automated mode
		self.carCount = 0
		self.emergencyFlag = None

		# load graphics for sign_pos_label
		self.stop_pic = QPixmap('Stop.png')
		# TODO resize pic so we don't need to scale it
		self.stop_pic = self.stop_pic.scaled(50,50,Qt.KeepAspectRatioByExpanding, Qt.FastTransformation) 
		self.slow_pic = QPixmap('Slow.jpg')
		# TODO resize pic so we don't need to scale it
		self.slow_pic = self.slow_pic.scaled(50,50,Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
		self.create_widget()



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

	def on_update_status(self, robot_name, car_count, emergency_flag):
		#print('car count is ' + car_count)
		#added for automated mode
		self.carCount = car_count
		self.emergencyFlag = emergency_flag

		self.car_count_label.setText(str(car_count))
		if (emergency_flag == '1'): #True
			self.on_emergency_approach()
		else: #False
			self.on_emergency_not_approach()

	def on_updated_frame(self):
		self.video_label.setPixmap(QPixmap(self.video_frame_file))

	def on_emergency_approach(self):
		self.emergency_desc_label.setStyleSheet('color: red')
		self.emergency_ans_label.setStyleSheet('color: red')
		self.emergency_ans_label.setText("Aproaching")
	
	def on_emergency_not_approach(self):
		self.emergency_desc_label.setStyleSheet('color: black')
		self.emergency_ans_label.setStyleSheet('color: black')
		self.emergency_ans_label.setText("None")

	# tells the robot to switch its sign from slow or stop
	def switch_sign(self):
		print(self.robot_name + " Change sign")
		if (self.sign_slow == True):
			print ("Controller sent STOP signal")
			self.robot_command_worker.add_command(robotcommands.CMD_ROBOT_STOP)
			self.robot_command_worker.add_command(robotcommands.CMD_DISPLAY_STOP)
			self.slow_stop_button.setText("Set to SLOW")
			self.slow_stop_button.setStyleSheet("color: orange")
			self.sign_pos_label.setPixmap(self.stop_pic)
			self.cbox.setCurrentIndex(0)
			self.sign_slow = False
			# added to unlock the buttons when one is at slow
			ButtonLock["button"] = False
		#changed else to elif to lock the buttons when one is at slow
		elif(self.sign_slow == False and not ButtonLock["button"]):
			print ("Controller sent SLOW signal")
			self.robot_command_worker.add_command(robotcommands.CMD_ROBOT_SLOW)
			self.robot_command_worker.add_command(robotcommands.CMD_ROBOT_RESET_COUNT)
			self.robot_command_worker.add_command(robotcommands.CMD_DISPLAY_PROCEED)
			self.slow_stop_button.setText("Set to STOP")
			self.slow_stop_button.setCheckable(True)
			self.slow_stop_button.setStyleSheet("color: red")
			self.sign_pos_label.setPixmap(self.slow_pic)
			self.cbox.setCurrentIndex(1)
			self.sign_slow = True
			# added to lock the buttons when one is at slow
			ButtonLock["button"] = True
		#message box pops up when operator tries to have both robots 			showing the slow signs
		else:
			self.msg = QMessageBox()
			self.msg.setIcon(QMessageBox.Information)
			self.msg.setText("Error:")
			self.msg.setDetailedText("You cannot have both robots showing the slow sign!")
			retval = self.msg.exec_()
			
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
	
	#added for automated mode
	def SetSignStatus(self,status):
		self.sign_slow = status
	#added for automated mode
	def GetSignStatus(self):
		return self.sign_slow
	def ReturnCarCount(self):
		return self.carCount
	def ReturnemergencyFlag(self):
		return self.emergencyFlag

#Automated mode class, run in separate thread, right now has a dumb changing sign just to check the gui
#It uses the RobotControl functions to show the decisioning
#It also pop up a second window which is supposed to show the decision/messages of the robots
class AutomatedMode(QThread):
	def __init__(self, r1,r2):
		super(QThread, self).__init__()
		self.r1 = r1
		self.r2 = r2
		self.counter = True
		self.r1SlowSign = False
		self.r2SlowSign = False

	def run(self):
		#getting sign status before changing them
		#the decisioning here is a dumb one, need to be changed
		self.r1SlowSign = self.r1.GetSignStatus()
		self.r2SlowSign = self.r2.GetSignStatus()
		self.r1CarCount = self.r1.ReturnCarCount()
		self.r2CarCount = self.r2.ReturnCarCount()
		self.r1emergencyFlag = self.r1.ReturnemergencyFlag()
		self.r2emergencyFlag = self.r2.ReturnemergencyFlag()

		print("car count of robot1 " + str(self.r1CarCount))
		print("car count of robot2 " + str(self.r2CarCount))
		#print("Emergency Flag of robot1 " + self.r1emergencyFlag)
		#print("Emergency Flag of robot2 " + self.r2emergencyFlag)

		self.count = 5
		self.time = QTimer()
		while self.counter:
			if (self.r1SlowSign == True):
				print ("Controller sent STOP signal")
				self.r1.SetSignStatus(True)
				self.r2.SetSignStatus(True)
				#uses robots control function just like assuming the button is pressed
				self.r1.switch_sign()
				self.r2.switch_sign()
			elif(self.r1SlowSign == False):
				print ("Controller sent SLOW signal")
				self.r1.SetSignStatus(False)
				# uses robots control function just like assuming the button is pressed
				self.r1.switch_sign()
				self.r2.SetSignStatus(True)
				# uses robots control function just like assuming the button is pressed
				self.r2.switch_sign()
			self.counter = False

#processing window for automated mode
#runs on a separate thread
#has settings to change the number of cars allowed to pass
#messages from robot decisioning need to be added
class ProcesssingWindow(QMainWindow,QThread):
	def __init__(self):
		super(QThread, self).__init__()
		#self.left = 500
		#self.top = 500
		#self.width = 840
		#self.height = 480

		#Settings for MenuBar
		bar = self.menuBar()
		file = bar.addMenu("Settings")
		ActionGroup = QActionGroup(bar,exclusive=True)
		Action = ActionGroup.addAction(QAction("5 cars each turn",bar,checkable=True))
		file.addAction(Action)
		Action =ActionGroup.addAction(QAction("10 cars each turn", bar, checkable=True))
		file.addAction(Action)
		Action =ActionGroup.addAction(QAction("15 cars each turn", bar, checkable=True))
		file.addAction(Action)
		ActionGroup.triggered[QAction].connect(self.processtrigger)

		self.text = QTextEdit()
		self.setCentralWidget(self.text)
		self.statusBar = QStatusBar()
		self.setWindowTitle("Automated Processing")
		self.setMinimumSize(840,480)
		self.setMaximumSize(840,480)
		#self.setGeometry(self.left, self.top, self.width, self.height)
		self.setStatusBar(self.statusBar)
		#function when the number of cars allowed to pass changes by the operator

	#need to add the change in car count
	def processtrigger(self, q):
		if (q.text() == "5 cars each turn"):
			self.statusBar.showMessage("5 cars each turn is alowed to pass")
			self.text.append("Changing number of cars allowed to pass to 5")
		if q.text() == "10 cars each turn":
			self.statusBar.showMessage("10 cars each turn is alowed to pass")
			self.text.append("Changing number of cars allowed to pass to 10")
		if q.text() == "15 cars each turn":
			self.statusBar.showMessage("15 cars each turn is alowed to pass")
			self.text.append("Changing number of cars allowed to pass to 15")
	def closeEvent(self, event):
		print("Closing Automated processing window")

class AdvancedCarCount(QWidget):
	def __init__(self):
		self.CAR_W = 50
		self.CAR_H = 50

		QWidget.__init__(self)
		self.car_pic = QPixmap("car.jpg")
		self.car_pic = self.car_pic.scaled(self.CAR_W, self.CAR_H,Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
		self.num_cars = 0
		
	def paintEvent(self, event):
		painter = QPainter(self)
		car_pixmap = QPixmap("car.jpg")

		painter.drawText(QRectF(0.0,0.0,50.0,50.0), Qt.AlignCenter|Qt.AlignTop, str(self.num_cars))

		i = 0
		while i < self.num_cars:
			painter.drawPixmap(50 + (self.CAR_W * i), 50, self.CAR_W, self.CAR_H, self.car_pic)
			i = i + 1


# Main application GUI
class MainWindow(QWidget):

	def __init__(self, net_adapter):
		QWidget.__init__(self)

		self.manual = True
		# get my ip stuff here
		server_address = robo_library.get_ip()
		print("Controller IP Address Found: " + server_address)

		self.lock = Lock()
		self.r1_count = 0
		self.r2_count = 0
		self.total_count = 0
		
		# create TCP/IP socket
		context = zmq.Context()

		location_service = IPLocationWorker(server_address, IP_LOCATION_PORT)
		location_service.start()

		self.r1 = RobotControl(ROBOT1_NAME, context, server_address, R1_VIDEO_PORT, R1_COMMAND_PORT, R1_COUNT_PORT)
		self.r2 = RobotControl(ROBOT2_NAME, context, server_address, R2_VIDEO_PORT, R2_COMMAND_PORT, R2_COUNT_PORT)
		self.r1.robot_status_worker.sig.connect(self.on_update_status)
		self.r2.robot_status_worker.sig.connect(self.on_update_status)
		
		vlayout = QVBoxLayout(self)

		# Auto/Manual Button and Count Layout
		count_layout = QVBoxLayout()
		self.Manual_Auto_button = QPushButton('Automated')
		self.Manual_Auto_button.clicked.connect(self.switch_mode)
		count_layout.addWidget(self.Manual_Auto_button)
		
		self.advanced_carcount = AdvancedCarCount()
		self.advanced_carcount.setMinimumSize(1280,100)
		self.advanced_carcount.setMaximumSize(1280,100)
		count_layout.addWidget(self.advanced_carcount)

		self.myProcesssingWindow = ProcesssingWindow()
		
		robot_layout = QHBoxLayout()
		robot_layout.addWidget(self.r1)
		robot_layout.addWidget(self.r2)

		vlayout.addLayout(count_layout)
		vlayout.addLayout(robot_layout)

		self.show()

#function for switching between manual and automated mode
	def switch_mode(self):
		if self.manual:
			print("switching mode to automated")
			self.Manual_Auto_button.setText("Manual")
			self.Manual_Auto_button.setStyleSheet('color: black')
			self.manual = False

			#message box, but it disables the robot control
			#self.msg = QMessageBox()
			#self.msg.setIcon(QMessageBox.Information)
			#self.msg.setText("Automated mode processing:")
			#self.msg.setDetailedText("The details are as follows:")
			#retval = self.msg.exec_()

			self.myProcesssingWindow.show()
			self.auto = AutomatedMode(self.r1,self.r2)
			self.auto.run()
		else:
			print("switch mode to manual")
			self.Manual_Auto_button.setText("Automated")
			self.Manual_Auto_button.setStyleSheet('color: green')
			self.manual = True
			self.myProcesssingWindow.hide()


	def on_update_status(self, robot_name, car_count, emergency_flag):
		if robot_name == ROBOT1_NAME:
			self.r1_count = int(car_count)
			self.r1_emergency_flag = bool(emergency_flag)
		else:
			self.r2_count = int(car_count)
			self.r2_emergency_flag = bool(emergency_flag)
		
		self.lock.acquire()
		self.total_count = abs(self.r1_count - self.r2_count)
		self.lock.release()
		self.advanced_carcount.num_cars = self.total_count
		self.advanced_carcount.update()


#Main 
if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = MainWindow(NET_ADAPTER)
	sys.exit(app.exec_())
