import io
import socket
import struct
import time
import picamera
from threading import Thread
import zmq

# Connect a client socket to my_server:8000 (change my_server to the
# hostname of your server)
my_server = '207.23.165.58' # edit me
client_socket = socket.socket()
client_socket.connect((my_server, 8000))  # For Robot 1 its 8000 and for robot 2 its 8001
# Make a file-like object out of the connection
connection = client_socket.makefile('wb')
print("Established pipe for video stream")

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://207.23.165.58:8002")
print("Established pipe for command listening")

def videoThread():
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
        
def processCommandThread():
    try:
        while True:
            socket.send_string('')
            message = socket.recv().decode('utf-8')
            print(message)
            time.sleep(1)
    finally:
        print("process command thread died")

if __name__ == "__main__":
    thread = Thread(target = videoThread)
    thread.start()
    print("Started video streaming thread")
    
    thread2 = Thread(target = processCommandThread)
    thread2.start()
print("Started process commands thread")
