import io
import socket
import struct
import time
import picamera
from threading import Thread
import zmq
import sys
import configparser
import robotcommands

#robot library
import Adafruit_PCA9685
import smbus #for i2c			# must enabled for SMBUS
import pigpio

# CONSTANTS
CONFIG_FILENAME = 'config.txt'  # configuration file name
VIDEO_WIDTH		= 640
VIDEO_HEIGHT	= 480

SMBUS_CONTROLLER = 1			# i2c bus controller
ARDUINO_I2C_ADDRESS = 0x04		# address of the arduino on the i2c bus

SERVER = "192.168.1.74"			# ip address of the controller

#add more commands here

# MESSAGES FROM ROBOT
READY = 'R'						# send after the robot establishes a connection and is ready for commands

# Configration class that reads configuraiton data from a file
class RobotConfig:
	GENERAL_SECTION = 'OPTIONS'
	SERVER_ADDRESS_CFG = 'server_address'
	STATUS_PORT_CVG = 'status_port'
	VIDEO_PORT_CFG = 'video_port'
	COMMAND_PORT_CFG = 'command_port'
	ROBOT_NAME_CFG = 'robot_name'
	HAS_SIGNBOARD_CFG = 'has_signboard'	#robot has a signboard
	SEND_VIDEO_CFG = 'send_video'		#send video to controller
	SEND_STATUS_CFG = 'send_status'		#send status emerg, count to controller
	RCV_COMMANDS_CFG = 'rcv_commands'	#receive commands from controller
	USE_PWM_CFG = 'use_pwm'				#enables motors
	USE_I2C_CFG = 'use_i2c'				#enables i2c
	
	def __init__(self, config_filename):
		self.config_filename = config_filename
		self.config = configparser.ConfigParser()
		self.config.read(config_filename)

	def get_option_str(self, parameter):
		value = self.config.get(self.GENERAL_SECTION, parameter, fallback="")

		if value != "":
			print("Found '" + parameter + "' config option in " + self.config_filename + " configuration file")
		else:
			print("Warning '" + parameter + "' config option not found in " + self.config_filename + " configuration file")
		
		return str(value)

	def get_option_bool(self, parameter):
		value = self.config.getboolean(self.GENERAL_SECTION, parameter, fallback="False")

		if value != "":
			print("Found '" + parameter + "' config option in " + self.config_filename + " configuration file")
		else:
			print("Warning '" + parameter + "' config option not found in " + self.config_filename + " configuration file")
		
		return bool(value)


# I2C 
# Communicate over I2C


def writeNumber(bus, address, value):
	bus.write_byte(address, value)
	#print("Sent to Arduino: ", value)

def readNumber(bus, address):
	number = bus.read_byte(address)
	return number

# I2C end

#------------------------------- Ada Fruit setup -----------------------
#pwm = Adafruit_PCA9685.PCA9685() # colin: running this line breaks my computer
servo_min = 150  # Min pulse length out of 4096
servo_max = 600  # Max pulse length out of 4096
def set_servo_pulse(channel, pulse):
    pulse_length = 1000000    # 1,000,000 us per second
    pulse_length //= 60       # 60 Hz
    print('{0}us per period'.format(pulse_length))
    pulse_length //= 4096     # 12 bits of resolution
    print('{0}us per bit'.format(pulse_length))
    pulse *= 1000
    pulse //= pulse_length
    pwm.set_pwm(channel, 0, pulse)
    pwm.set_pwm_freq(50)
#------------------------------- Lowers Robot stop hand  -----------------------

def arm_down(cur_pos, end_pos):
	pos = cur_pos
	step_size = 10

	while pos > end_pos:
		pos = pos - step_size
		if (pos < servo_min):
			pos = servo_min
		pwm.set_pwm(0, 0, pos)
		time.sleep(.2)

	pwm.set_pwm(0, 0, servo_min)


def send_video(socket):
	
	try:
		camera = picamera.PiCamera()
		camera.resolution = (VIDEO_WIDTH, VIDEO_HEIGHT)
		# let the camera warm up for 2 seconds
		time.sleep(2)

		# Make a file-like object out of the connection
		connection = socket.makefile('wb')
		stream = io.BytesIO()
		for foo in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
			# Write the length of the capture to the stream and flush to
			# ensure it actually gets sent
			connection.write(struct.pack('<L', stream.tell()))
			connection.flush()
			# Rewind the stream and send the image data over the wire
			stream.seek(0)
			connection.write(stream.read())
			# Reset the stream for the next capture
			stream.seek(0)
			stream.truncate()
		
		# Write a length of zero to the stream to signal we're done
		connection.write(struct.pack('<L', 0))
	except socket.error as ex:
		print(ex)
	finally:
		connection.close()
		socket.close()
        

# The process_command function receives commands from the controller
# and tells the robot to perform each action.  When each action is completed
# it sends a message describing what action was done back to the controller.
# socket is the network socket use to communicate with the controller
# pwm_enabled True enables the motors, Falase allows the motors to be disabled if necessary (for testing)
# i2c_enabled True enables I2c bus, flase allow the i2c to be turned off for testing without i2c.
#	only messages are sent to robot
# bus is the i2c bus controller on the pi used to communicate with the arduinos
#
# LINDA
# (1) add signboard commands to this function ( if you like, you can add a command for each different signboard message)
# (3) Add a command to reset the Arduino's emergency vehicle approaching to False (similar to how car count is reset
#	you can get Colin's help if you to adjust the aruino code
# (4) update the RobotCommandWorker in gui.py so that it sends the correct commands over the network
# (5) use constants for the robot commands instead of hard coding them 
#	example: if command == robotcommands.CMD_ROBOT_STOP: 
#	instead of : if command = '1':
# (6) any new robot commands should be added to the robotcommands.py example
#	example: CMD_SIGNBOARD_STOP = '55'
# (7) Fix RobotCOmmandWorker in gui.py so that its run command has a shorter delay < 0.5 seconds
def process_command(socket, pwm_enabled, i2c_enabled, bus):

	if pwm_enabled:
		print(robot_name + " motors are enabled")
	else:
		print(robot_name + " motors are disabled")

	try:
		# let the controller know the robot is ready for commands
		print("Waiting for robot ready")
		socket.send(READY.encode('utf-8'))
		print("Robot Ready")
		running = True
		while running:
			command = socket.recv().decode('utf-8')
			print("DEBUG: " + str(command))
			if command == robotcommands.CMD_ROBOT_STOP:
				print("set RoboFlagger to 'Stop' configuration")
				if pwm_enabled:
					pwm.set_pwm(0, 0, 400)
					pwm.set_pwm(1, 0, servo_min)
				else:
					print("PWM disabled")
				socket.send_string("RoboFlagger in 'Stop' configuration")

			elif command == robotcommands.CMD_ROBOT_SLOW:
				print("set RoboFlagger to 'Slow' Configuration")
				if pwm_enabled:
					arm_down(400, servo_min)
				else:
					print("PWM disabled")
				socket.send_string("RoboFlagger in 'Slow' configuration")

			elif command == robotcommands.CMD_ROBOT_RESET_COUNT: # reset car count
				print("Resetting car count from arduino")
				if i2c_enabled:
					writeNumber(bus, ARDUINO_I2C_ADDRESS, 2)
					time.sleep(0.05)
					count = readNumber(bus, ARDUINO_I2C_ADDRESS)
					print("Count is : " + count)
				else:
					print("i2c disabled")
				socket.send_string("Car count reset to zero")
			else:
				print("command not supported")
				socket.send_string("Command not supported")
		
	except KeyboardInterrupt:
		print("process command interrupted")
	try:
		socket.close()
		sys.exit(0)
	except SystemExit:
		os._exit(0)

# This function sends the status of the robot's carcount and emergency vehicle status to the robot
# at a regular intervals.  Both carcount and emergency vehicle status are retrived from the arduino
# using I2C.  The Arduino should set a variable to True when there is an emergency vehicle approaching
# it should stay True until the controller resets it to False.
# - current car count (number)
# - IR emergency vehicle sensor status. should be True if there is an emergency vehicle approaching
#   or False if there isn't an emergency vehcile approaching
# - IR emergency vehicle sensor status stays True until the controller resets the status
def publish_robot_status(publisher, i2c_enabled, bus):
	try:
		while True:
			print("Publishing car count from arduino")
			writeNumber(bus,ARDUINO_I2C_ADDRESS, 1)
			time.sleep(0.05)
			carCount = readNumber(bus,ARDUINO_I2C_ADDRESS)
			print("From Arduino, I received car count: ", carCount)
			publisher.send_multipart([robot_name.encode('utf-8'),str(carCount).encode('utf-8')])
			time.sleep(0.5)
			print("Published car count to %s" % robot_name)

	except KeyboardInterrupt:
		print("process command interrupted")
	try:
		publisher.close()
		sys.exit(0)
	except SystemExit:
		os._exit(0)

if __name__ == "__main__":
	# gets cfg options from a config file instead of hardcoding 
	# then we wont need to have two versions of this file (one for each robot)
	rc = RobotConfig(CONFIG_FILENAME)
	robot_name = rc.get_option_str(rc.ROBOT_NAME_CFG)
	print("Robots name is " + robot_name)

	context = zmq.Context()

	i2c_enabled = rc.get_option_bool(rc.USE_I2C_CFG)
	pwm_enabled = rc.get_option_bool(rc.USE_PWM_CFG)

	bus = None #i2c bus controller
	if i2c_enabled:
		smbus.SMBus(SMBUS_CONTROLLER)

	if rc.get_option_bool(rc.SEND_VIDEO_CFG):
		# Socket for sending video frames to controller
		video_socket = socket.socket()
		video_socket.connect((SERVER, int(rc.get_option_str(rc.VIDEO_PORT_CFG))))
		print("Established pipe for video stream")

		# pass the required socket to the thread in an argument
		video_thread = Thread(target = send_video, kwargs=dict(socket=video_socket))
		video_thread.start()
		print("Started video streaming thread")
	else:
		print("Sending Video Disabled")
	

	if rc.get_option_bool(rc.RCV_COMMANDS_CFG):		
		# processes commands from the controller
		command_socket = context.socket(zmq.REQ)
		command_socket.connect("tcp://" + SERVER + ":" + rc.get_option_str(rc.COMMAND_PORT_CFG))
		print(robot_name + " : Established pipe for receiving commands")
		command_thread = Thread(target = process_command, kwargs=dict(socket=command_socket, 
																	pwm_enabled=pwm_enabled, 
																	i2c_enabled=i2c_enabled, 
																	bus=bus))
		command_thread.start()
		print(robot_name + " : Started command processing thread")
	else:
		print("Receiving Commands Disabled")

	# FRANK
	# (1) change the network model from request reply to publish subscribe
	# the robot is the publisher while the controller is the subscriber
	# The CarCountWorker in gui.py receives the status information from the robot
	# It should be able to work with any changes you make here to the sockets
	# (2) please give publisher a better name
	# (3) fix publish_robot_status function so that it works with the pub sub network model
	# (4) fix CarCountWorker in gui.py so it works with the publish subscribe model.
	# (5) the interval for status updates should be .5 seconds
	if rc.get_option_bool(rc.SEND_STATUS_CFG):
		#Sending status of robot to controller (carcount, emerg)
		publisher = context.socket(zmq.PUB)
		publisher.connect("tcp://" + SERVER + ":" + rc.get_option(rc.STATUS_PORT_CFG))	
		publish_status_thread = Thread(target = publish_robot_status, kwargs=dict(socket=publisher,																	bus=bus))
		publish_status_thread.start()
	else:
		print("Sending Robot Status Updates Disabled")
