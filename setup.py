try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

config = {
	'description'      : 'Daemonizer',
	'author'           : 'Aaron Holmes',
	'url'              : 'http://aaronholmes.net',
	'download_url'     : 'https://github.com/aholmes/PythonDaemon',
	'author_email'     : 'aaron@aaronholmes.net',
	'version'          : '0.1',
	'install_requires' : ['nose'],
	'packages'         : ['Daemon'],
	'scripts'          : [],
	'name'             : 'Daemon'
}

setup(**config)
