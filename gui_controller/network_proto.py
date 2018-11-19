import socket
import sys
import zmq
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    print("Your Computer IP Address is:" + IPAddr)
except socket.gaierror:
    # this means could not resolve the host
    print("there was an error resolving the host")
    sys.exit()
L = len(IPAddr)
lastTwoDigits = int(IPAddr[L-2:])
fixedDigits = IPAddr[:L-2]


# create TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
options = lastTwoDigits
digits = str(options)
counter = 1



def test_socket(ip):
    
    socket_obj = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    socket_obj.settimeout(0.1)
    result = socket_obj.connect_ex((ip,8000))
    socket_obj.close()
    if (result != 0):
        print("Did not connect succesfully")
        return False
    else:
        print("Did connect")
        return True




result = False
number = 0
while result == False:
    
    fixedDigits = '10.0.0.'  
    digits =  str(number)
    IP = '%s%s'% (fixedDigits,digits)
    print("The IP is %s"% IP)
    result = test_socket(IP)
    number += 1
