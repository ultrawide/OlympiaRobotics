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
# Connect a client socket to my_server:8000 (change my_server to the
# hostname of your server)
my_server = '207.23.201.64' # edit me
client_socket = socket.socket()
client_socket.connect((my_server, 8000))  # For Robot 1 its 8000 and for robot 2 its 8001
# Make a file-like object out of the connection
connection = client_socket.makefile('wb')
print("Established pipe for video stream")

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://" + my_server + ":8002")
print("Established pipe for command listening")

# Communicate over I2C
bus = smbus.SMBus(1) # 1 indicates /dev/i2c-1

address = 0x08
address_arduino = 0x04

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
            #message = socket.recv().decode('utf-8')
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
            elif message == "7": #get car count
                print("Retrieving car count from arduino")
                writeNumber(address_arduino, 1)
                time.sleep(0.05)
                carCount = readNumber(address_arduino)
                print("From Arduino, I received car count: ", carCount)
                socket.send(str(carCount).encode('utf-8'))
                message = socket.recv()
            #else:
                 #socket.send(b"Option not implemented")
    except KeyboardInterrupt:
        print("process command interrupted")
        try:
            socket.close()
            sys.exit(0)
        except SystemExit:
            os._exit(0)

if __name__ == "__main__":
    video_thread = Thread(target = sendVideo)
    video_thread.start()
    print("Started video streaming thread")
    
    command_thread = Thread(target = processCommand)
    command_thread.start()

