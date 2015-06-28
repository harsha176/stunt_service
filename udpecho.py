#! /usr/bin/env python

# Client and server for udp (datagram) echo.
#
# Usage: udpecho -s [port]            (to start a server)
# or:    udpecho -c host [port] <file (client)

import sys
from socket import *

ECHO_PORT = 50000 + 7
BUFSIZE = 1024

def main():
	if len(sys.argv) < 2:
		usage()
	if sys.argv[1] == '-s':
		server()
	elif sys.argv[1] == '-c':
		client()
	else:
		usage()

def usage():
	sys.stdout = sys.stderr
	print 'Usage: udpecho -s [port]            (server)'
	print 'or:    udpecho -c host [port] <file (client)'
	sys.exit(2)

def server():
	if len(sys.argv) > 2:
		port = eval(sys.argv[2])
	else:
		port = ECHO_PORT
	s = socket(AF_INET, SOCK_DGRAM)
	s.bind(('', port))
	print 'udp echo server ready'

	# Registration records
	reg_records = dict()
	while 1:
		data, addr = s.recvfrom(BUFSIZE)
		data = data.rstrip()
		print 'server received', `data`, 'from', `addr`
                # parse data, if it is registration message then register it
                # if it is a connect request message, check if the destination is a valid
		# address, if it is then send remote's public address as response to both the client 
		# and server
                msg_type = data.split(":")[0]
		msg_data = data.split(":")[1:]
		msg_response = msg_type
		if msg_type == 'MSG_REG':
			print "Got registration message with data: {0}".format(msg_data)
                        # parse the response and get dst private ip address
                        dst_priv_addr = msg_data[0]
			reg_records[dst_priv_addr] = addr

			# send response
			msg_response = "{0}:{1}".format(msg_type, "Successfully registered client: {0}".format(dst_priv_addr))
		elif msg_type == 'MSG_CONNECT':
			# Get src dst private IP from the msg_data
			src_priv_addr = msg_data[0]
			dst_priv_addr = msg_data[1]
			
			# If src is not registered then register the source
			if not src_priv_addr in reg_records.keys():
				reg_records[src_priv_addr] = addr
			
			if not dst_priv_addr in reg_records.keys():
				msg_response = "{0}:{1}".format(msg_type, "Failed to find destination: {0}".format(dst_priv_addr))
			else:
				# send response to src and dst
				# send to dst first and then to src
				print "Sending MSG_CONNECT_FORWARD to ", reg_records[dst_priv_addr]
				s.sendto("{0}:{1}".format('MSG_CONNECT_FORWARD', reg_records[src_priv_addr]), reg_records[dst_priv_addr])
				print "Sending MSG_CONNECT_FORWARD to ", reg_records[src_priv_addr]
				s.sendto("{0}:{1}".format('MSG_CONNECT_FORWARD', reg_records[dst_priv_addr]), reg_records[src_priv_addr])

		# Send acknowledgement to client
		s.sendto(msg_response, addr)

def client():
	if len(sys.argv) < 3:
		usage()
	host = sys.argv[2]
	if len(sys.argv) > 3:
		port = eval(sys.argv[3])
	else:
		port = ECHO_PORT

	if len(sys.argv) > 4:
		priv_ip = sys.argv[4]

	addr = host, port
	s = socket(AF_INET, SOCK_DGRAM)
	s.bind(('', 0))
	print 'udp echo client ready, reading stdin'
	while 1:
		line = sys.stdin.readline()
		if not line:
			break
		s.sendto('MSG_REG:{0}'.format(priv_ip), addr)
		data, fromaddr = s.recvfrom(BUFSIZE)
		print 'client received', `data`, 'from', `fromaddr`

main()
