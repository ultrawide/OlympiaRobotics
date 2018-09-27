import pygame.camera
import pygame.image
import zmq
import time
import base64

cameras = pygame.camera.list_cameras()
webcam = pygame.camera.Camera(camera[0])
webcam.start()

context = zmq.Context()
print("Connecting to server...")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")
i = 0

# encode 2 different images
f0 = open("mountains1.jpg", 'rb')
f1 = open("mountains2.jpg", 'rb')
bytes1 = bytearray(f0.read())
image1 = base64.b64encode(bytes1)
bytes2 = bytearray(f1.read())
image2 = base64.b64encode(bytes2)
f0.close()
f1.close()

while True:

	
	try:
		if i == 0:
			socket.send(image1)
			i = 1
		else:
			socket.send(image2)
			i = 0

		time.sleep(.1)
		socket.recv()

	except KeyboardInterrupt:
		f0.close()
		f1.close()
		print("\n\nBye bye\n")
		break
