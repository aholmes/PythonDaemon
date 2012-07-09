import os, signal, sys
from signal import SIG_DFL, SIG_IGN, SIGHUP, SIGCHLD, SIGINT
from time import sleep

class Daemon(object):
	(STATE_IDLE, STATE_STOPPED, STATE_RUNNING, STATE_TERMINATED, STATE_WORKING) = (1, 2, 4, 8, 16)

	state_names = {1 : 'STATE_IDLE', 2 : 'STATE_STOPPED', 4 : 'STATE_RUNNING', 8 : 'STATE_TERMINATED', 16 : 'STATE_WORKING'}

	_state = 0

	prefork            = False
	number_of_children = 0
	child_callback     = lambda self, work = {}: None 
	parent_callback    = lambda self: None 
	shutdown           = lambda self: None

	# a list of dictionaries: [{'a':'a', 'b:'b'}, {'c':'c'}]
	work_data          = []

	pid           = 0
	children_pids = {}

	def __init__(self, config = {}):
		self.state = Daemon.STATE_IDLE
		self._sig_handle()

		if 'prefork' in config:
			self.prefork = config['prefork']

		if 'number_of_children' in config:
		        self.number_of_children = config['number_of_children']

		if 'child_callback' in config:
		        self.child_callback = config['child_callback']

		if 'parent_callback' in config:
		        self.parent_callback = config['parent_callback']

		if 'work_data' in config:
			self.work_data = config['work_data']

		if 'shutdown' in config:
			self.shutdown = config['shutdown']

	def _sig_handle(self, reset=False):
		if reset == True:
			signal.signal(SIGCHLD,  SIG_DFL)
		else:
			signal.signal(SIGHUP,  self._SIG_HUP)
			signal.signal(SIGCHLD, self._SIG_CHLD)
			signal.signal(SIGINT,  self._SIG_INT)

	def up(self):
		self.state = Daemon.STATE_RUNNING

		self._fork()

		self._parent()

		return True

	def down(self):
		self.state = Daemon.STATE_STOPPED

	def work(self, work):
		if type(work) == list:
			self.work_data = work
		elif type(work) == dict:
			self.work_data = [work]

	def _child(self):
		self.children_pids = {}
		self.number_of_children = 0

		self._sig_handle(True)

		# this requires that the child callback doesn't return None, otherwise we loop in the child
		if self.child_callback(self, self.work_data) == None:
			while self.state[0] == Daemon.STATE_RUNNING:
				sleep(1)

		# the child finished - exit
		sys.exit(0)

	def _parent(self):
		# this requires that the parent callback doesn't return None, otherwise we loop in the parent
		if self.parent_callback(self) == None:
			while self.state[0] == Daemon.STATE_RUNNING:
				sleep(1)

		# the parent finished - exit
		sys.exit(0)

	def _fork(self):
		while (self.prefork or self.work_data) and len(self.children_pids) < self.number_of_children:
			work = self.work_data.pop() if self.work_data else None

			pid = os.fork()

			self.pid = os.getpid()

			if pid == 0:
				self.work_data = [work] if work else []
				self._child()
				return None;
			else:
				self.children_pids[pid] = self.STATE_RUNNING		

	def _SIG_HUP(self, signum, frame):
		for names in dir(self):
			attr = getattr(self,names)
			if not callable(attr):
				print names,':',attr

		print 'State: %d\n' % self.state
		print 'Config:\n'
		print '\tPrefork: %r\n' % self.prefork
		print '\tNumber of children%r\n' % self.number_of_children
		print '\tChild callback%r\n' % self.child_callback
		print '\tParent callback%r\n' % self.parent_callback
		print 'Children:\n%r' % self.children_pids
		return None

	def _SIG_CHLD(self, signum, frame):
		terminated_child = os.wait3(0)

		print 'Terminated: %d' % terminated_child[0]

		del self.children_pids[terminated_child[0]]

		self._fork()

		return None

	def _SIG_INT(self, signum, frame):
		self.state = Daemon.STATE_STOPPED

		if not self.children_pids:
			return None

		self.shutdown(self)

		for pid, state in self.children_pids.items():
			if state == self.STATE_TERMINATED:
				continue

			print 'Killing: %d' % pid
			os.kill(pid, SIGINT)

		return None

	def _get_state(self):
		return [self._state, self.state_name]

	def _set_state(self, state):
		self._state      = state
		self.state_name = Daemon.state_names[self._state]

	state = property(_get_state, _set_state)
