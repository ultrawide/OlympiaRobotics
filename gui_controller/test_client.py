# Client only used for testing
# Removes any dependence on PWM and I2C
# Simulates performing robot movement and communication over i2c
# simulates reading sensor data
# no video stream
import io
import socket
import struct
import time
import picamera
from threading import Thread
import zmq
import sys

#CONSTANTS
CONTROLLER_ADDRESS = "192.168.0.1" 
VIDEO_PORT = 8000
COMMAND_PORT = 8001
        
def processCommand(socket):
	try:
		while True:
			socket.send(''.encode('utf-8'))
			message = socket.recv()
			if message == "5":
				print("set RoboFlagger to 'Stop' configuration")

			elif message == "6":
				print("set RoboFlagger to 'Slow' Configuration")

			elif message == "8": # reset car count
				print("Resetting car count from arduino")

			else:
				 print("command not supported")

	except KeyboardInterrupt:
		print("process command interrupted")
		
	try:
		socket.close()
		sys.exit(0)
	except SystemExit:
		os._exit(0)

if __name__ == "__main__":
	
	# Socket for recieving commands
	context = zmq.Context()
	command_socket = context.socket(zmq.REQ)
	command_socket.connect("tcp://" + CONTROLLER_ADDRESS + ":" + COMMAND_PORT)  
	print("Established pipe for command listening")

	# pass the required socket to the thread in an argument
	command_thread = Thread(target = processCommand, socket = command_socket)
	command_thread.start()

