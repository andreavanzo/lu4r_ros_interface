#!/usr/bin/env python
# encoding=utf8

# encoding=utf8

import socket
import sys
import requests
import json
from math import radians, sin, cos

reload(sys)  
sys.setdefaultencoding('utf8')
 
conn = None
host = ''
port = 5001
HEADERS = {'content-type': 'application/json'}

def listener():
	global semantic_map
	global conn
	lu4r_ip = "127.0.0.1"
	lu4r_port = "9090"
	lu4r_url = 'http://' + lu4r_ip + ':' + str(lu4r_port) + '/service/nlu'
	entities = "{\"entities\":[]}"
	currentFragment = ''
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
					data = data.replace("KEEP_AWAKE\n","")
					if len(data) == 0:
						continue
				if '$' in data:
					currentFragment = data[1:-1]
					continue				
				if currentFragment == "HOME":
					continue				
				elif currentFragment == "JOY":
					rho_theta = data.split()
					rho = float(rho_theta[0])
					theta = radians(float(rho_theta[1]))
					#motion.linear.x = max_tv * rho * sin(theta)
					#motion.angular.z = max_rv * -1 * rho * cos(theta)
					#v_joyopad.publish(motion)
				elif currentFragment == "SLU":
					toSend = {'hypo': data, 'entities': entities}
					response = requests.post(lu4r_url, toSend, headers = HEADERS)
					print response.text
				else:
					print "Unknown service"
			else:
				print 'Disconnected from ' + addr[0] + ':' + str(addr[1])
				currentFragment = ''
				break
	s.close()

if __name__ == '__main__':
	listener()

