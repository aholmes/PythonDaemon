import Daemon
import socket, os, select, sys, curses, locale, struct
from time import sleep

class Server(object):
	socket = None

	daemon_config = {}

	address = ''
	port    = 1227
	daemon  = None

	child_callback     = lambda self, work = {}: None 
	parent_callback    = lambda self: None 

	def __init__(self, config = {}, daemon_config = {}):
		self.daemon_config = {
			'prefork'            : True,
			'number_of_children' : 2,
			#'work_data':[{'test':1,'test2':'test'}, {'a':'a'}],
			# bring up the parent and child when the daemon is forked
			'parent_callback'    : self.parent,
			'child_callback'     : self.child,
			'shutdown'           : self.shutdown
		}

		# Daemon config
		if 'prefork' in daemon_config:
			self.daemon_config.prefork = daemon_config['prefork']

		if 'number_of_children' in daemon_config:
		        self.daemon_config.number_of_children = daemon_config['number_of_children']

		if 'child_callback' in daemon_config:
		        self.daemon_config.child_callback = daemon_config['child_callback']

		if 'parent_callback' in daemon_config:
		        self.daemon_config.parent_callback = daemon_config['parent_callback']

		if 'work_data' in daemon_config:
			self.daemon_config.work_data = daemon_config['work_data']

		if 'shutdown' in daemon_config:
			self.daemon_config.shutdown = daemon_config['shutdown']

		# Server config
		if 'address' in config:
			self.address = config['address']

		if 'port' in config:
			self.port = config['port']

		if 'child_callback' in config:
		        self.child_callback = config['child_callback']

		if 'parent_callback' in config:
		        self.parent_callback = config['parent_callback']

	def up(self):
		self.Daemon = Daemon.Daemon(self.daemon_config)

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('dd', 1, 0))
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		while True:
			try:
				self.socket.bind((self.address, self.port))
				break
			except socket.error, (errno, message):
				# temporarily unavailable
				if errno == 48:
					print 'Waiting for socket to become available'
					sleep(1)
				else:
					print '%d %s' % (errno, message)
					sys.exit(-1)

		self.socket.listen(1)
		self.socket.setblocking(0)

		self.Daemon.up()

	# main parent loop. Handle watching children.
	def parent(self, daemon):
		while daemon.state[0] == daemon.STATE_RUNNING:
			sleep(1)

		return True

	# main child loop. Work on work
	def child(self, daemon, work):
		read_sockets = [self.socket]

		while daemon.state[0] == daemon.STATE_RUNNING:
			if daemon.work_data:
				daemon.state = daemon.STATE_WORKING
				print '%d\'s Work: %r\n' % (os.getpid(), daemon.work_data)

				# pretend like we're working
				while True:
					sleep(1)
					continue;
			else:
				# wait for a ready socket
				try:
					read, write, error = select.select(read_sockets, [], [], 60)
				except select.error, (errno, message):
					# interrupted system call
					if errno == 4:
						sys.exit(0)

					print 'IOError, or other exception %r - %r\n' % (errno, message)
					sys.exit(-1)

				for conn in read:
					# received new connection, add to list of read sockets to get data from it
					if conn == self.socket:
						# accept the socket and add it to our list of ready sockets
						try:
							client, address = self.socket.accept()
						except socket.error, (errno, message):
							if errno == 35:
								continue

							print 'IOError, or other exception %r - %r' % (errno, message)

						read_sockets.append(client)
					# selected a ready client, handle it
					else:
						print '%d Reading from connection\n' % os.getpid()
						data = conn.recv(1024)
						
						# if we read data, do something
						if data:
							print 'Got data'
							conn.send(data)
						else:
							print 'No data'
							conn.close()
							read_sockets.remove(conn)

	def shutdown(self, daemon):
		self.socket.close()
		return None
