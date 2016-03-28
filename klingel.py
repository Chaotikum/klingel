import pyaudio
import wave
import sys
import os
import random
import socket
import struct
import time
import threading
from subprocess import call

def playsound(fn):
	print("play", fn)
	call(["paplay", fn])
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

def run(data):
	print(data)

	if data == "ring":
		putfile('/sys/class/gpio/gpio11/value', '0')
		playsound("/root/ring.wav")
		threading.Timer(60, putfile('/sys/class/gpio/gpio11/value', '1')).start()

	if data == "open":
		playsound("/root/open.wav")
	
	if data == "summ":
		putfile('/sys/class/gpio/gpio11/value', '1')
		playsound("/root/summ.wav")

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
	(data, seq) = data.split(",")

	try:
	  l = lastseq[data]
	except:
	  l = 0
	
	if seq != l:
		run(data)
		lastseq[data] = seq

