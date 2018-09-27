import cv2
import zmq
import time
import base64

context = zmq.Context()
print("Connecting to server...")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")
i = 0

cam = cv2.VideoCapture(0)

# encode 2 different images
#f0 = open("mountains1.jpg", 'rb')
#f1 = open("mountains2.jpg", 'rb')
#bytes1 = bytearray(f0.read())
#image1 = base64.b64encode(bytes1)
#bytes2 = bytearray(f1.read())
#image2 = base64.b64encode(bytes2)
#f0.close()
#f1.close()

while True:

	try:
		ret_val, img = cam.read()
		cv2.imshow('my webcam', img)
		#img_scaled = cv2.resize(img, (640,480))
		cv2.imwrite('image_c.jpg', img_scaled)
		
		f = open('image_c.jpg', 'rb')
		bytes = bytearray(f.read())
		image = base64.b64encode(bytes)
		socket.send(image)

		time.sleep(.1)
		socket.recv()

	except KeyboardInterrupt:
		cam.release()

		print("\n\nBye bye\n")
		break
