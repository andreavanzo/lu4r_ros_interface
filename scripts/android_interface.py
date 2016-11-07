#!/usr/bin/env python
# encoding=utf8

# encoding=utf8

import rospy
from sensor_msgs.msg import Joy
from std_msgs.msg import String
import socket
import sys
import re
import requests
import actionlib
import tf
import rospkg
import json
import time
import datetime
from math import radians, sin, cos
from move_base_msgs.msg import *
from tf.transformations import quaternion_from_euler
from geometry_msgs.msg import Pose2D
from geometry_msgs.msg import Twist
import xmltodict
import pprint
import os
import xdg_extract as xdg
from subprocess import call

reload(sys)  
sys.setdefaultencoding('utf8')
 
conn = None
semantic_map = {}
goal = Pose2D()
HOST = ''
PORT = 5001
CHAIN_URL = 'http://127.0.0.1:9091/service/nlu'
HEADERS = {'content-type': 'application/json'}
rospack = rospkg.RosPack()
dir = rospack.get_path('android_interface')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print 'Socket created'
try:
	s.bind((HOST, PORT))
except socket.error as msg:
	print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
	sys.exit()
print 'Socket bind complete'
s.listen(10)
print 'Socket now listening on port ' + str(PORT)

def clean_string(to_clean):
	to_clean = to_clean.replace('\'',' ')
	to_clean = to_clean.replace('è','e')
	to_clean = to_clean.replace('é','e')
	to_clean = to_clean.replace('ì','i')
	to_clean = to_clean.replace('à','a')
	to_clean = to_clean.replace('ò','o')
	to_clean = to_clean.replace('ù','u')
	return to_clean

def simple_move(pose):
    sac = actionlib.SimpleActionClient('/move_base', MoveBaseAction )
	goal = MoveBaseGoal()
	goal.target_pose.pose.position.x = float(pose.x)
	goal.target_pose.pose.position.y = float(pose.y)
	quaternion = tf.transformations.quaternion_from_euler(0, 0, float(pose.theta))
	goal.target_pose.pose.orientation.x = quaternion[0]
	goal.target_pose.pose.orientation.y = quaternion[1]
	goal.target_pose.pose.orientation.z = quaternion[2]
	goal.target_pose.pose.orientation.w = quaternion[3]
	goal.target_pose.header.frame_id = '/map'
	goal.target_pose.header.stamp = rospy.Time.now()
	print 'Wait for service'
	sac.wait_for_server()
	print 'sending goal'
	sac.send_goal(goal)
	print 'Wait for result'
	sac.wait_for_result()
	result = int( sac.get_state())
	if(result == 3):
		return 'DON'
	else:
		return 'ERR'

def listener():
	global semantic_map
	global conn
	motion = Twist()
	rospy.init_node('android_interface_node', anonymous = True)
	rospy.Subscriber('joy', Joy, callback)
	rospy.Subscriber("speech", String, speech_callback)
	v_joyopad = rospy.Publisher('cmd_vel', Twist, queue_size = 1)
	max_tv = rospy.get_param("~max_tv", 0.6)
	max_rv = rospy.get_param("~max_rv", 0.8)
	PORT = rospy.get_param("~port", 5001)
	CHAIN_URL = 'http://' + rospy.get_param("~lu4r_ip", '127.0.0.1') + ':' + rospy.get_param("~lu4r_port", '9090') + '/service/nlu' 
	sem_map = rospy.get_param('~semantic_map','semantic_map.txt')
	ENTITIES = open(dir + "/semantic_maps/" + sem_map).read()
	json_string = json.loads(ENTITIES)
	for entity in json_string['entities']:
		semantic_map[entity['type']] = Pose2D()
		semantic_map[entity['type']].x = entity["coordinate"]["x"]
		semantic_map[entity['type']].y = entity["coordinate"]["y"]
		semantic_map[entity['type']].theta = entity["coordinate"]["angle"]
		print entity['type']
		print semantic_map[entity['type']]
		print
	currentFragment = ''
	while not rospy.is_shutdown():
		print "Waiting for connection"
		conn, addr = s.accept()
		print 'Connected with ' + addr[0] + ':' + str(addr[1])
		while not rospy.is_shutdown():
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
					motion.linear.x = max_tv * rho * sin(theta)
					motion.angular.z = max_rv * -1 * rho * cos(theta)
					v_joyopad.publish(motion)
				elif currentFragment == "SLU":
					toSend = {'hypo': data, 'entities': ENTITIES}
					print "MESSAGE TO SEND "+ data
					response = requests.post(CHAIN_URL, toSend, headers = HEADERS)
					predicates = xdg.find_predicates(response.text)
					#conn.send(predicates+'\r\n')
					print predicates
				else:
					print "Unknown service"
			else:
				print 'Disconnected from ' + addr[0] + ':' + str(addr[1])
				currentFragment = ''
				break
	s.close()

if __name__ == '__main__':
	listener()

