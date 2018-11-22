import RPi.GPIO as GPIO
import time

startTimerFlag = False

# Specify in your code which number-system is being used
GPIO.setmode(GPIO.BOARD)

# Set pins as input or output
# 38: GPIO20, 40: GPIO21
GPIO.setup(38, GPIO.OUT)
GPIO.setup(40, GPIO.IN, GPIO.PUD_UP)

# to write a pin to high ex. 
start = 0
end = 0

while True:
    if (GPIO.input(40) == 0 and startTimerFlag == False):
        start = time.time()
        startTimerFlag = True
    elif (GPIO.input(40) == 1):
        startTimerFlag = False
    elif ((end - start) >= 5):
        GPIO.output(38, GPIO.HIGH)
        print("Please power off :)")

    end = time.time()
    print(end - start)

