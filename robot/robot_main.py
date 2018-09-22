#   Name:robo_main.py
#   File lives: On raspberrypi
#   Binds REP socket to tcp://*:5555
#
#   Expects b"from" from RoboServoController.py ,
#   Returns 'command' executed and moves servos
#
from __future__ import division
import time
import zmq
import Adafruit_PCA9685
import smbus
import time
import pigpio

bus = smbus.SMBus(1) # 1 indicates /dev/i2c-1

address = 0x06

def writeNumber(value):
	bus.write_byte(address, value)
	#print("Sent to Arduino: ", value)

def readNumber():
	number = bus.read_byte(address)
	return number


#------------------------------- Ada Fruit setup -----------------------
# Uncomment to enable debug output.
#import logging
#logging.basicConfig(level=logging.DEBUG)

# Initialise the PCA9685 using the default address (0x40).
pwm = Adafruit_PCA9685.PCA9685()

# Alternatively specify a different address and/or bus:
#pwm = Adafruit_PCA9685.PCA9685(address=0x41, busnum=2)

# Configure min and max servo pulse lengths
servo_min = 150  # Min pulse length out of 4096
servo_max = 600  # Max pulse length out of 4096

# Helper function to make setting a servo pulse width simpler.
def set_servo_pulse(channel, pulse):
    pulse_length = 1000000    # 1,000,000 us per second
    pulse_length //= 60       # 60 Hz
    print('{0}us per period'.format(pulse_length))
    pulse_length //= 4096     # 12 bits of resolution
    print('{0}us per bit'.format(pulse_length))
    pulse *= 1000
    pulse //= pulse_length
    pwm.set_pwm(channel, 0, pulse)

# Set frequency to 60hz, good for servos.
pwm.set_pwm_freq(50)
#------------------------------- Ada Fruit setup END -----------------------
#arm_down() lowers robot stop hand
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


context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

loop = True
while loop:
    message = socket.recv()
    print("Received request: %s" % message)


    if message == "1":
        print "raise stop hand"
        # "Move servo on channel O between extremes."
        pwm.set_pwm(0, 0, 400)  # stop hand
        socket.send(b"Raise stop hand")
    
    elif message == "2":
        print "lower stop hand"
        arm_down(400, servo_min)
        socket.send(b"Lower stop hand")

    elif message == "3":
        print "rotate sign to stop"
        pwm.set_pwm(1, 0, servo_max)
        socket.send(b"Rotate sign to stop")

    elif message == "4":
        print "rotate sign to slow"
        pwm.set_pwm(1, 0, servo_min)
        socket.send(b"Rotate sign to slow")
    elif message == "5":
        print "set RoboFlagger to 'Stop' configuration"
        pwm.set_pwm(0, 0, 400)
        pwm.set_pwm(1, 0, servo_min)
        socket.send(b"Set RoboFlagger to 'Stop' configuration")

    elif message == "6":
        print "set RoboFlagger to 'Slow' Configuration"
        pwm.set_pwm(1, 0, servo_max)
        arm_down(400, servo_min)
        #pwm.set_pwm(1, 0, servo_max)
        socket.send(b"set RoboFlagger to 'Slow' configuration")

    elif message == "7":
        print "not implemented yet"
	socket.send(b"not implemented")
    elif message == "8":
        print "get current car count"
	writeNumber(4)
        time.sleep(100)
        count = readNumber()
        print "car count = %d"% count
        socket.send(b"car count = %d"% count)
    elif message == "9":
        writeNumber(3)
        time.sleep(100)
        count = readNumber()
        print "car count = %d"% count
        socket.send(b"car count = %d"% count)

    elif message == "10":
        loop = False
        print "Disconnect command invoked by controller"
        socket.send(b"Disconnecting from robot\n")
    else:
            socket.send(b"Option not implemented (should never get here)")
print "Disconnecting from socket"
socket.close()
