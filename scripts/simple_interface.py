#!/usr/bin/env python
# encoding=utf8

# encoding=utf8

import socket
import sys
import requests
import os

reload(sys)  
sys.setdefaultencoding('utf8')
 
conn = None
host = ''
port = 5001
HEADERS = {'content-type': 'application/json'}


def listener(port, lu4r_ip, lu4r_port, semantic_map):
	global conn
	port = int(port)
	lu4r_url = 'http://' + lu4r_ip + ':' + str(lu4r_port) + '/service/nlu'
	print lu4r_url
	working_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	entities = open(working_dir + "/semantic_maps/" + semantic_map).read()
	current_fragment = ''
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	print 'Socket created'
	try:
		s.bind((host, port))
	except socket.error as msg:
		print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
		sys.exit()
	print 'Socket bind complete'
	s.listen(10)
	
	while True:
		print "Waiting for connection on port " + str(port)
		conn, addr = s.accept()
		print 'Connected with ' + addr[0] + ':' + str(addr[1])
		while True:
			data = conn.recv(512)
			print 'Received: '+data
			if data and not data.isspace():
				if "KEEP_AWAKE" in data:
					data = data.replace("KEEP_AWAKE\n", "")
					if len(data) == 0:
						continue
				if '$' in data:
					current_fragment = data[1:-1]
					continue				
				if current_fragment == "HOME":
					continue				
				elif current_fragment == "JOY":
					rho_theta = data.split()
				elif current_fragment == "SLU":
					to_send = {'hypo': data, 'entities': entities}
					response = requests.post(lu4r_url, to_send, headers=HEADERS)
					print response.text
				else:
					print "Unknown service"
			else:
				print 'Disconnected from ' + addr[0] + ':' + str(addr[1])
				current_fragment = ''
				break
	s.close()

if __name__ == '__main__':
	for option in sys.argv[1:]:
		if "_lu4r_port:=" in option:
			lu4r_port = str(option).replace("_lu4r_port:=", "")
		elif "_lu4r_ip:=" in option:
			lu4r_ip = str(option).replace("_lu4r_ip:=", "")
		elif "_port:=" in option:
			port = str(option).replace("_port:=", "")
		elif "_semantic_map:=" in option:
			semantic_map = str(option).replace("_semantic_map:=", "")
	listener(port, lu4r_ip, lu4r_port, semantic_map)

