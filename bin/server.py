import Daemon
import socket, os, select, sys, curses, locale, struct
from time import sleep

locale.setlocale(locale.LC_ALL, '')

# configure the daemon
s = Daemon.Server()

print 'Server started at PID %d' % os.getpid()

# bring the daemon up
s.up()
