from distutils.core import setup, Extension

jdwp = Extension(
	'andbug.jdwp', ['jdwp/jdwp.c', 'jdwp/wire.c']
)

setup(
	name = 'andbug',
	version = '0.1',
	description = 'The AndBug scriptable Android debugger',
	author = 'Scott Dunlop',
	author_email = 'swdunlop@gmail.com',
	packages = ['andbug'],
	ext_modules = [jdwp]
)