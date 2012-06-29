import Daemon
import socket, os, select, sys
from time import sleep

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

try:
	os.remove('/tmp/PythonDaemonSocket')
except OSError:
	pass

s.setblocking(0)
s.bind('/tmp/PythonDaemonSocket')
s.listen(1)

# main parent loop. Handle watching children.
def parent(daemon):
	while daemon.state[0] == daemon.STATE_RUNNING:
		print 'Our Children: %r\n' % daemon.children_pids
		sleep(1)

	return True

# main child loop. Work on work
def child(daemon, work):
	read_sockets = [s]

	while daemon.state[0] == daemon.STATE_RUNNING:
		if daemon.work_data:
			daemon.state = daemon.STATE_WORKING
			print '%d\'s Work: %r\n' % (os.getpid(), daemon.work_data)

			# pretend like we're working
			while True:
				sleep(1)
				continue;
		else:
			print '%d Waiting for connection\n' % os.getpid()

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
				if conn == s:
					print '%d Accepting connection\n' % os.getpid()
					try:
						client, address = s.accept()
					except socket.error, (errno, message):
						if errno == 35:
							continue

						print 'IOError, or other exception %r - %r' % (errno, message)

					read_sockets.append(client)
				# selected a ready client, handle it
				else:
					print '%d Reading from connection\n' % os.getpid()
					data = conn.recv(1024)
					if data:
						conn.send(data)
					else:
						conn.close()
						read_sockets.remove(conn)

# configure the daemon
d = Daemon.Daemon({
	'prefork':True,
	'number_of_children':4,
	#'work_data':[{'test':1,'test2':'test'}, {'a':'a'}],
	'parent_callback':parent,
	'child_callback':child
})

print 'Server started at PID %d' % os.getpid()

# bring the daemon up
d.up()
