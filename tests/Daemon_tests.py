from nose.tools import *
import Daemon

def setup():
	print 'Setup!'

def teardown():
	print 'Tear down!'

def test_basic():
	print 'I ran!'
