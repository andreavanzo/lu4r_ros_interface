#!/usr/bin/env python

# NOTE: this example requires PyAudio because it uses the Microphone class

import sys
import select
import os
import speech_recognition as sr
import json

r = None
m = None


def init():
	global r
	global m
	r = sr.Recognizer()
	m = sr.Microphone()
	with m as source:
		print "Configuring the background noise..."
		r.adjust_for_ambient_noise(source)
		print "Background noise acquired"


def listen():
	with m as source:
		audio = r.listen(source)
	try:
		# for testing purposes, we're just using the default API key
		# to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
		# instead of `r.recognize_google(audio)`
		# r.recognize_google(audio)
		prova = r.recognize_google(audio, None, "en", True)
		print prova['alternative']
		for test in prova:
			print test[0]
		#print r.recognize_google(audio, None, "en-US", True)
	except sr.UnknownValueError:
		print("Google Speech Recognition could not understand audio")
	except sr.RequestError as e:
		print("Could not request results from Google Speech Recognition service; {0}".format(e))


if __name__ == '__main__':
	init()
	while True:
		print "Press Enter to start listening, type \"quit\" to exit..."
		line = raw_input()
		if "quit" in line:
			break
		print "..say something!"
		listen()
