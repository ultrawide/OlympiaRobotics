#   robo_servo_controller.py
#   File lives: On laptop controller
#
#   Connects REQ socket to tcp://<your_ip_on_your_pi>:5555
#
#   Sends command to RoboServo.py
#   Recieves command acknowledgement

import zmq

context = zmq.Context()

def print_menu():       ## Your menu design here
    print 30 * "-" , "MENU" , 30 * "-"
    print("RoboFlagger menu")
    print("(1) raise stop hand")
    print("(2) lower stop hand")
    print("(3) rotate sign to stop")
    print("(4) rotate sign to slow")
    print("(5) set RoboFlagger to 'Stop' configuration")
    print("(6) set RoboFlagger to 'Slow' configuration")
    print("(7) set RoboFlagger in automatic mode")
    print("(8) get car count")
    print("(9) clear car count")
    print("(10) quit program")
    print 67 * "-"

# using zeromq request model
#connect("tcp:<ip_from_rpi>:5555")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

loop = True
while loop:
    print_menu()
    choice = input("Input command for RoboFlagger \n")

    if choice == 1:
        
        socket.send(b"1")
    elif choice == 2:
        socket.send(b"2")
    elif choice == 3:
        socket.send(b"3")
    elif choice == 4:
        socket.send(b"4")
    elif choice == 5:
        socket.send(b"5")
    elif choice == 6:
        socket.send(b"6")
    elif choice == 10:
        socket.send(b"10")
    else:
        print "Command not yet implemented"
        continue
    
    message = socket.recv()
    print ("Robo Reply %s: " % message)
    if choice == 10:
        loop = False
        print "Shutting down"

socket.close()

