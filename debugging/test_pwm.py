import io
import socket
import struct
import time
import picamera
from threading import Thread, Lock
import zmq
import sys
import configparser
import robotcommands
import RPi.GPIO as GPIO
import robo_library

#robot library
import Adafruit_PCA9685
import smbus #for i2c			# must enabled for SMBUS
import pigpio

pwm = Adafruit_PCA9685.PCA9685() # colin: running this line breaks my computer
pwm.set_pwm_freq(50)

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
#------------------------------- Lowers Robot stop hand  -----------------------

def arm_down(cur_pos, end_pos):
	pos = cur_pos
	step_size = 10
	print("Arm down command")
	while pos > end_pos:
		pos = pos - step_size
		if (pos < servo_min):
			pos = servo_min
		pwm.set_pwm(0, 0, pos)
		time.sleep(.2)

pwm.set_pwm(0, 0, servo_min)
pwm.set_pwm(0, 0, 400)

#arm_down(400, servo_min)
#pwm.set_pwm(1,0,servo_max)
#pwm.set_pwm(1, 0, servo_min)
