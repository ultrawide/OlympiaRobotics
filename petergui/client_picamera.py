from picamera import PiCamera
import zmq
from time import sleep
import base64
import io

context = zmq.Context()
print("Connecting to server...")
socket = context.socket(zmq.REQ)
socket.connect("tcp://207.23.206.18:8000")
print("\n Connected")

camera = PiCamera(resolution=(640,480))

while True:

	try:
            camera.start_preview()
	    stream = io.BytesIO()
            camera.capture(stream, format='jpeg', use_video_port=True)
	    stream.seek(0)
            camera.stop_preview()
            image = base64.b64encode(stream.getvalue())
            socket.send(image)
            socket.recv()

	except KeyboardInterrupt:
		#cam.release()

		print("\n\nBye bye\n")
		break
