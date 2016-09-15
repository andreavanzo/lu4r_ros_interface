#!/usr/bin/env python
# encoding=utf8

# encoding=utf8

import rospy
from sensor_msgs.msg import Joy
from std_msgs.msg import String
import socket
import sys
import aiml
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
 
k = aiml.Kernel()
conn = None
semantic_map = {}
goal=Pose2D()
HOST = ''
PORT = 5002
CHAIN_URL = 'http://127.0.0.1:9091/service/nlu'
HEADERS = {'content-type': 'application/json'}
rospack = rospkg.RosPack()
dir=rospack.get_path('android_interface')

# UNIRETE SERVICES URLS
MAIN_URL="http://localhost:8080/unirete-services/rest"
COMPANY_URL=MAIN_URL+"/company"
AREA_URL=MAIN_URL+"/company"
PROGRAM_URL=MAIN_URL+"/program"

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
k.learn("wedding.aiml")

azienda_confirm=""

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
	
	
	result=int( sac.get_state())
	if( result==3):
		return 'DON'
	else:
		return 'ERR'
def callback(data):
	if data.buttons[0] == 1:
		reply = k.respond('GREEN')
		conn.send(reply + '\r\n')
	if data.buttons[1] == 1:
		reply = k.respond('RED')
		conn.send(reply + '\r\n')
	if data.buttons[2] == 1:
		reply = k.respond('BLUE')
		conn.send(reply + '\r\n')
	if data.buttons[3] == 1:
		reply = k.respond('YELLOW')
		conn.send(reply + '\r\n')

def speech_callback(data):
	if data.data == "tag":
		reply = k.respond('TAG')
		conn.send(reply + '\r\n')
	if data.data == "follow":
		reply = k.respond('FOLLOW')
		conn.send(reply + '\r\n')

def get_events_reply(json_string):
	if len(json_string) > 1:
		reply = "Questi sono gli eventi in calendario. "
	else:
		reply = "Questo è l'evento in calendario. "			
	for num,event in enumerate(json_string):
		reply = reply + str((num+1)) + ": " + event["title"]
		if event["room"] != "":
			reply = reply + " in sala " + event["room"]
		reply = reply + ", "
	reply = reply[:-2]
	reply = reply +  '. ' + k.respond('AIUTO');
	return reply
	
def get_companies_reply(json_string, sector_name):
	reply = 'Queste sono alcune aziende che si occupano di ' + sector_name + '. '
	for company in json_string:
		reply = reply + company + ', '
	reply = reply[:-2]
	reply = reply + '. ' + k.respond('INFOAZIENDASETTORE');
	return reply

def listener():
	global semantic_map
	global conn
	motion = Twist()
	rospy.init_node('android_interface_node', anonymous=True)
	rospy.Subscriber('joy', Joy, callback)
	rospy.Subscriber("speech", String, speech_callback)
	v_joyopad = rospy.Publisher('cmd_vel', Twist, queue_size=1)
	max_tv = rospy.get_param("~max_tv", 0.6)
	max_rv = rospy.get_param("~max_rv", 0.8)
	aiml_base = rospy.get_param('~aiml_base','wedding.aiml')
	k.learn(dir + "/aiml_bases/" + aiml_base)
	k.respond('STARTINTERACTION')
	sem_map = rospy.get_param('~semantic_map','semantic_map.txt')
	ENTITIES = open(dir + "/semantic_maps/" + sem_map).read()
	json_string=json.loads(ENTITIES)
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
	#while 1:
		print "Waiting for connection"
		conn, addr = s.accept()
		print 'Connected with ' + addr[0] + ':' + str(addr[1])
		while not rospy.is_shutdown():
		#while 1:
			data = conn.recv(512)
			print 'Received: '+data
			if data and not data.isspace():
				if "KEEP_AWAKE" in data:
					data=data.replace("KEEP_AWAKE\n","")
					if len(data)==0:
						continue
				if '$' in data:
					currentFragment=data[1:-1]
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
				elif currentFragment == "NLP":
					toSend={'hypo': data, 'entities': ENTITIES}
					print "MESSAGE TO SEND "+ data
					response = requests.post(CHAIN_URL, toSend, headers=HEADERS)
					predicates = xdg.find_predicates(response.text)
					#print response.text
					print predicates
					for predicate_name in predicates:
						predicate = predicates[predicate_name]
						if predicate_name == 'Motion':
							if 'Goal' in predicate:
								for elem in predicate['Goal']:
									if elem in semantic_map:
										print semantic_map[elem]
										simple_move(semantic_map[elem])
							elif 'Direction' in predicate:
								if 'avanti' in predicate['Direction']:
									motion.linear.x = 6.0
									motion.angular.z = 0.0
									v_joyopad.publish(motion)
									motion.linear.x = 6.0
									motion.angular.z = 0.0
									v_joyopad.publish(motion)
						elif predicate_name == 'Change_direction':
							for elem in predicate['Direction']:
								if 'sinistra' in elem:
									motion.linear.x = 0.0
									motion.angular.z = 1.57
									v_joyopad.publish(motion)
								elif 'destra' in elem:
									motion.linear.x = 0.0
									motion.angular.z = -1.57
									v_joyopad.publish(motion)
				elif currentFragment == "DIA":
					json_hypotheses = json.loads(data)
					best_hypo = json_hypotheses["hypotheses"][0]["transcription"]
					print 'You said:' + best_hypo
					reply = re.sub(' +',' ',k.respond(clean_string(best_hypo)))
					if '[CALLAZIENDA]' in reply:
						company_name = reply.split(']')[1]
						response = requests.get(COMPANY_URL + '/name?q='+company_name+'&full='+data)
						print response.text
						json_string=json.loads(response.text)
						if len(json_string) > 0:
							if  json_string["textIntro"] is not None and json_string["textIntro"] != "":
								reply = "Queste sono le informazioni che ho su: " + json_string["title"] + ". " + json_string["textIntro"] + '. ' + k.respond('AIUTO');
							else:
								reply = "Non ho informazioni su "+json_string["title"] +". Vai sul sito web di unirete per ulteriori informazioni. " + k.respond('AIUTO');
						else:
							reply = "Mi spiace, non ho informazioni su: " + company_name + ". " + k.respond("INFOAZIENDA")
					elif '[CALLSETTORE]' in reply:
						sector_name = reply.split(']')[1]
						response = requests.get(COMPANY_URL + '/sector?q='+sector_name)
						print response.text
						json_string=json.loads(response.text)
						if len(json_string) > 0:
							if len(json_string)>1:
								reply = get_companies_reply(json_string, sector_name)
							else:
								azienda_confirm = json_string[0]
								reply = 'Questa è l\'unica azienda che ho trovato che si occupa di ' + sector_name + '. ' + azienda_confirm	+ ". "					
								reply = reply + 'Vuoi che te ne parli?' + k.respond('ACONFIRM');
						else:
							reply = "Mi spiace, non ho trovato nessuna azienda per: " + sector_name + ". " + k.respond("INFOSETTORE")
					elif '[CALLEVENT]' in reply:
						print reply
						splitted = reply.split(']')[1].split('|')
						day = splitted[0]
						time = splitted[1]
						if 'now' in day:
							response = requests.get(PROGRAM_URL + '/now')
							print response.text
							if "title" in response.text:
								json_string=json.loads(response.text)							
								reply = get_events_reply(json_string)
							else:
								reply = "Mi spiace, non ci sono eventi in programma ora"
						elif 'next' in day:
							response = requests.get(PROGRAM_URL + '/next')
							print response.text
							if "title" in response.text:
								json_string=json.loads(response.text)
								reply = get_events_reply(json_string)
							else:
								reply = "Mi spiace, non ci sono eventi in programma prossimamente"
						else:
							if 'today' in day:
								date = datetime.date.today()
								day_string = "oggi"
							elif 'tomorrow' in day:
								date = datetime.date.today() + datetime.timedelta(days=1)
								day_string = "domani"
							if time.count(':') == 0:
								time = time + ':00:00'
							else:
								time = time + ':00'
							response = requests.get(PROGRAM_URL + '/datetime?date=' + date.strftime('%Y-%m-%d') + '&time=' + time)
							print response.text
							time_string = time[:-3].replace(":", " e ")
							if "title" in response.text:
								json_string=json.loads(response.text)
								reply = get_events_reply(json_string)
							else:
								reply = "Mi spiace, non ci sono eventi in programma per "+day_string +" alle "+time_string+". " + k.respond('AIUTO');
					elif '[CALLSETTOREOAZIENDA]' in reply:
						query = reply.split(']')[1]
						print query
						response = requests.get(COMPANY_URL + '/comorsector?q='+query)
						print response.text
						json_string=json.loads(response.text)
						if len(json_string) == 0:
							reply = "Mi spiace, non ho trovato nessuna informazione per: " + query + ". " + k.respond("AIUTO")
						else:
							if json_string[0] == "COMPANY":
								azienda_confirm=json_string[1]
								reply = "Ho trovato l'azienda " + azienda_confirm + ". Vuoi che te ne parli?" + ". " + k.respond("ACONFIRM")							
							else:
								sector_confirm = json_string[1]
								reply = "Ho trovato il settore " + sector_confirm + ". Vuoi più informazioni?" + ". " + k.respond("SCONFIRM")
					elif '[AZIENDACONFIRMED]' in reply:
						response = requests.get(COMPANY_URL + '/name?q='+azienda_confirm+'&full='+data)
						print response.text
						json_string=json.loads(response.text)
						if  json_string["textIntro"] is not None and json_string["textIntro"] != "":
							reply = "Queste sono le informazioni che ho su: " + json_string["title"] + ". " + json_string["textIntro"] + '. ' + k.respond('AIUTO');
						else:
							reply = "Non ho informazioni su "+json_string["title"] +". Vai sul sito web di unirete per ulteriori informazioni. " + k.respond('AIUTO');
						#reply = "Queste sono le informazioni che ho su: " + json_string["title"] + ". " + json_string["textIntro"] + '. ' + k.respond('AIUTO');
						azienda_confirm=""
					elif '[SETTORECONFIRMED]' in reply:
						response = requests.get(COMPANY_URL + '/sector?q='+sector_confirm)
						print response.text
						json_string=json.loads(response.text)
						reply = get_companies_reply(json_string, sector_name)
						sector_confirm=""
					elif '[COMMAND]' in reply:
						toSend={'hypo': data, 'entities': ENTITIES}
						response = requests.post(CHAIN_URL, toSend, headers=HEADERS)
						print(response.text)
						reply = k.respond('AIUTO')
					print 'Robot said:' + reply
					conn.send(reply + '\r\n')
				else:
					print "Unknown service"
					conn.send('Unknown service\r\n')
			else:
				print 'Disconnected from ' + addr[0] + ':' + str(addr[1])
				currentFragment = ''
				break
	s.close()

if __name__ == '__main__':
	listener()

