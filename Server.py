import socket
import sys
import zmq

try:
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    print("Your Computer IP Address is:" + IPAddr)
except socket.gaierror:
    # this means could not resolve the host
    print("there was an error resolving the host")
    sys.exit()

# create TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# bind the socket to the port 8000
server_address = (IPAddr, 8000)
print ('starting up on %s port %s' % server_address)
sock.bind(server_address)

#connecting through zmq (could not test it as I don't have the pi
context = zmq.Context()
s = context.socket(zmq.REP)
s.bind("tcp://"+IPAddr+":8002")

# listen for incoming connections (server mode) with 3 connection at a time
sock.listen(3)

while True:
    # wait for a connection
    print ('waiting for a connection')
    connection, client_address = sock.accept()
    try:
        # show who connected to us
        print ('connection from', client_address)

        # receive the data in small chunks and print it
        while True:
            data = connection.recv(64)
            #dataS = connectionS.recv(64)   #need pi
            if data:
                # output received data
                print ("Data: %s" % data)
                #print("Data: %s" % dataS)   #need pi
            else:
                # no more data -- quit the loop
                print ("no more data.")
                break
    finally:
        # Clean up the connection
        connection.close()

