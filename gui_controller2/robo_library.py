import socket, struct, fcntl

SIOCGIFADDR = 0x8915

def get_ip(iface = 'wlp3s0'):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	ifreq = struct.pack('16sH14s'.encode('utf-8'), iface.encode('utf-8'), socket.AF_INET, ('\x00'*14).encode('utf-8'))
	try:
		res = fcntl.ioctl(sock.fileno(), SIOCGIFADDR, ifreq)
	except:
		return None
	ip = struct.unpack('16sH2x4s8x', res)[2]
	return socket.inet_ntoa(ip)
