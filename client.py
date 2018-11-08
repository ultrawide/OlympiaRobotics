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
while True:
    try:
        LL = len(str(options))
        if LL==1:
            digits = "0" + str(options)
        else:
            digits =  str(options)       
        IP = "%s%s"% (fixedDigits,digits)
        print("check if can connect to: " + IP)
        sock.connect((IP, 8000))
        print("connection successful")
        # define example data to be sent to the server
        temperature_data = ["15", "22", "21", "26", "25", "19"]
        for entry in temperature_data:
            print ("data: %s" % entry)
            new_data = str("temperature: %s\n" % entry).encode("utf-8")
            sock.send(new_data)

            # wait for two seconds
            time.sleep(2)

            # close connection
        sock.close()
        break
    except:
        if counter%2 == 0:
            options = options -counter
        else:
            options = options +counter
        counter = counter+1
        if str(options)==lastTwoDigits:
            options = options+1
        if len(str(options)) >=3:
            print("No network found")
            break
        else:
            continue




#server_address = ('192.168.1.69', 8000)
#sock.connect(server_address)

#could not test it since I don't have the pi
context = zmq.Context()
sockK = context.socket(zmq.REQ)
sockK.connect("tcp://"+'192.168.1.69'+":8002")


