import io
import socket
import struct
import time
import picamera
from threading import Thread
import zmq
import sys

#robot library
import Adafruit_PCA9685
import smbus #for i2c
import pigpio

# Constants
ARDUINO_I2C_ADDRESS = 0x04

# TODO: be able to scan for the controllers IP address
# or configure the networking on the controller so that
# its ip is static.  What we want to do is turn on the
# robot and have it connect to the controller without
# having to manually edit settings.  I'm thinking we setup
# another pi to act as a router.
SERVER ADDRESS = '207.23.201.64' # Controller's IP Address

# Communicate over I2C
bus = smbus.SMBus(1) # 1 indicates /dev/i2c-1

def writeNumber(address, value):
	bus.write_byte(address, value)
	#print("Sent to Arduino: ", value)

def readNumber(address):
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

def sendVideo():
    try:
        camera = picamera.PiCamera()
        camera.resolution = (640, 480)
        # let the camera warm up for 2 seconds
        time.sleep(2)

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
        client_socket.close()
        
def processCommand():
    try:
        while True:
            socket.send(''.encode('utf-8'))
            message = socket.recv()
            if message == "5":
                print("set RoboFlagger to 'Stop' configuration")
                pwm.set_pwm(0, 0, 400)
                pwm.set_pwm(1, 0, servo_min)
                #socket.send(b"Set RoboFlagger to 'Stop' configuration")
		
            elif message == "6":
                print("set RoboFlagger to 'Slow' Configuration")
                pwm.set_pwm(1, 0, servo_max)
                arm_down(400, servo_min)
                #pwm.set_pwm(1, 0, servo_max)
                #socket.send(b"set RoboFlagger to 'Slow' configuration")
		
            elif message == "8": # reset car count
                print("Resetting car count from arduino")
                writeNumber(ARDUINO_I2C_ADDRESS, 2)
                time.sleep(0.05)
                carCount = readNumber(ARDUINO_I2C_ADDRESS)
                socket.send_string("")
                message = socket.recv()
		
            else:
                 print("command not supported")
			
    except KeyboardInterrupt:
        print("process command interrupted")
        try:
            socket.close()
            sys.exit(0)
        except SystemExit:
            os._exit(0)

def carCount():
    try:
        while True:
            socket2.send(''.encode('utf-8'))
            message = socket2.recv()
            if message == "7": #get car count
		print("Retrieving car count from arduino")
		writeNumber(ARDUINO_I2C_ADDRESS, 1)
		time.sleep(0.05)
		carCount = readNumber(ARDUINO_I2C_ADDRESS)
		print("From Arduino, I received car count: ", carCount)
		socket2.send(str(carCount).encode('utf-8'))
		message = socket2.recv()
		
    except KeyboardInterrupt:
	print("process command interrupted")
	try:
	    socket.close()
	    sys.exit(0)
	except SystemExit:
	    os._exit(0)

if __name__ == "__main__":
	# Socket for sending video frames to controller
	client_socket = socket.socket()
	client_socket.connect((my_server, 8001))  # For Robot 1 its 8000 and for robot 2 its 8001
	# Make a file-like object out of the connection
	connection = client_socket.makefile('wb')
	print("Established pipe for video stream")

	# User a configuration file to load the Robot's port configuration settings
	# this way we can use the same python script for each robot.  Each robot
	# will have a configuration file with its own custom settings.  See configuration.py
	# for an example
	
	# Socket for recieving commands
	context = zmq.Context()
	socket = context.socket(zmq.REQ)
	socket.connect("tcp://" + my_server + ":8002")
	print("Established pipe for command listening")

	# TODO Remove this socket 
	# For sending car count for robot 1
	socket2 = context.socket(zmq.REQ)
	socket2.connect("tcp://" + my_server + ":8004") # robot1: port 8003, robot2: port 8004 	
	
	# pass the required socket to the thread in an argument
	video_thread = Thread(target = sendVideo)
	video_thread.start()
	print("Started video streaming thread")

	# pass the required socket to the thread in an argument
	command_thread = Thread(target = processCommand)
	command_thread.start()

	# we need to combine the funcitonality of car count thread with
	# the that of the command thread.  Command thread will be driven
	# by the controller
	car_count_thread = Thread(target = carCount)
	car_count_thread.start()
