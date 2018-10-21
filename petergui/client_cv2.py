import cv2
import zmq
import time
import base64
import io

context = zmq.Context()
print("Connecting to server...")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")
i = 0

cam = cv2.VideoCapture(0)

while True:

	try:
		ret_val, cam_image = cam.read()
		#img_scaled = cv2.resize(img, (640,480))
		retval, jpg_image = cv2.imencode(".jpg", cam_image)
		image_encoded = base64.b64encode(jpg_image)
		socket.send(image_encoded)

		time.sleep(.1)
		socket.recv()

	except KeyboardInterrupt:
		cam.release()

		print("\n\nBye bye\n")
		break
