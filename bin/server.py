import Daemon
import socket, os, select, sys, curses, locale, struct
from time import sleep

locale.setlocale(locale.LC_ALL, '')

def handle_client(server):
	data = server.recv(1024)

	while data:
		print 'Got data'
		server.send(data)

		data = server.recv(1024)

	print 'No data'
	server.close()

# configure the daemon
s = Daemon.Server({
	'child_callback':handle_client
})

print 'Server started at PID %d' % os.getpid()

# bring the daemon up
s.up()
