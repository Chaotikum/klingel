import pyaudio
import wave
import sys
import os
import random
import socket
import struct
import time
import requests
import json
from threading import Timer, Thread
from subprocess import call, Popen

def playsound(fn):
	print("play", fn)
	Popen(["paplay", fn])
	return
	CHUNK = 1024

	wf = wave.open(fn, 'rb')

	p = pyaudio.PyAudio()

	stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
			channels=wf.getnchannels(),
			rate=wf.getframerate(),
			output=True)

	# read data
	data = wf.readframes(CHUNK)

	while len(data) > 0:
	    stream.write(data)
	    data = wf.readframes(CHUNK)

	stream.stop_stream()
	stream.close()

	p.terminate()

def receiver(group, port):
	addrinfo = socket.getaddrinfo(group, None)[0]
	s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind(('', port))

	group_bin = socket.inet_pton(addrinfo[0], addrinfo[4][0])
	mreq = group_bin + struct.pack('@I', 0)
	s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

	return s

group = "ff02::6004"
port = 6004
ifname = "eth0"

s = receiver(group, port)

locked_oben = True
locked_unten = True

def reset_locks():
	global locked_open, locked_unten
	locked_oben = True
	locked_unten = True

def genugdavon():
	putfile('/sys/class/gpio/gpio11/value', '1')
	playsound("/root/wrong.wav")

def check_locks():
	try:
		r = requests.get('https://padlock.nobreakspace.org/api/locks', cert=('klingel.crt', 'klingel.key'), verify=False)
		for x in r.json():
			if x['id'] == '261175':
				locked_unten = x['locked']

			if x['id'] == '334EC1':
				locked_oben = x['locked']

		print("Locks", locked_unten, locked_oben)
	except:
		pass

timer = None

def run(data, d=None):
	global timer
	print(data)

	if data == "ring":
		if int(d) == 1:
			if timer:
				timer.cancel()

			timer = Timer(60, genugdavon)
			timer.start()

			check = Thread(target=check_locks)
			check.start()

			putfile('/sys/class/gpio/gpio11/value', '0')

			playsound("/root/ring-bb.wav")
		else:
			playsound("/root/ring-fis.wav")
	

	if data == "open":
#		if not locked_oben:
		playsound("/root/open.wav")
	
	if data == "summ":
		if timer:
			timer.cancel()

#		if not locked_oben:
		putfile('/sys/class/gpio/gpio11/value', '1')
		playsound("/root/summ.wav")
#		else:
#			playsound("/root/locked.wav")

def putfile(file, data):
	f = open(file, 'w')
	f.write(data)
	f.close()

try:
	putfile('/sys/class/gpio/export', '11')
except:
	pass

putfile('/sys/class/gpio/gpio11/direction', 'out')
putfile('/sys/class/gpio/gpio11/value', '1')

lastseq = dict()
while True:
	data, sender = s.recvfrom(1500)
	while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
	data = data.decode('utf-8')
	x = data.split(",")
	try:
		data = x[0]
	except:
		data = None

	try:
		seq = x[1]
	except:
		seq = None

	try:
		d = x[2]
	except:
		d = None

	try:
	  l = lastseq[data]
	except:
	  l = 0
	
	if seq != l:
		run(data, d)
		lastseq[data] = seq

