from picamera import PiCamera
import zmq
from time import sleep
import base64

context = zmq.Context()
print("Connecting to server...")
socket = context.socket(zmq.REQ)
socket.connect("tcp://207.23.206.18:8000")
print("\n Connected")

camera = PiCamera(resolution=(400,300))


while True:

	try:
            camera.start_preview()
            camera.capture('/home/pi/capstone/OlympiaRobotics/petergui/image.jpg')
            camera.stop_preview()
            f = open('image.jpg','rb')
            bytes = bytearray(f.read())
            image = base64.b64encode(bytes)
            socket.send(image)
            socket.recv()

	except KeyboardInterrupt:
		#cam.release()

		print("\n\nBye bye\n")
		break
