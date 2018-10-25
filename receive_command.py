import socket
import zmq
import base64
import time
import sys
import os

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://10.42.0.255:8000")

while True:
	data = socket.recv()
	socket.send_string('')
	print("received character: " )
	print(data)


