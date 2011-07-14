## Copyright 2011, IOActive, Inc. All rights reserved.
##
## AndBug is free software: you can redistribute it and/or modify it under 
## the terms of version 3 of the GNU Lesser General Public License as 
## published by the Free Software Foundation.
##
## AndBug is distributed in the hope that it will be useful, but WITHOUT ANY
## WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS 
## FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for 
## more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with AndBug.  If not, see <http://www.gnu.org/licenses/>.

from distutils.core import setup, Extension, Command

# Used by TestCommand and CleanCommand
from unittest import TextTestRunner, TestLoader
from glob import glob
from os.path import splitext, basename, join as pjoin, walk
import os

class TestCommand(Command):
	# From: http://da44en.wordpress.com/2002/11/22/using-distutils/
    user_options = []

    def initialize_options(self):
        self._dir = os.getcwd()

    def finalize_options(self):
        pass

    def run(self):
        testfiles = [ ]
        for t in glob(pjoin(self._dir, 'tests', '*.py')):
            if not t.endswith('__init__.py'):
                testfiles.append('.'.join(
                    ['tests', splitext(basename(t))[0]])
                )

        tests = TestLoader().loadTestsFromNames(testfiles)
        t = TextTestRunner(verbosity = 1)
        t.run(tests)

class CleanCommand(Command):
	# From: http://da44en.wordpress.com/2002/11/22/using-distutils/
    user_options = [ ]

    def initialize_options(self):
        self._clean_me = [ ]
        for root, dirs, files in os.walk('.'):
            for f in files:
                if f.endswith('.pyc'):
                    self._clean_me.append(pjoin(root, f))

    def finalize_options(self):
        pass

    def run(self):
        for clean_me in self._clean_me:
            try:
                os.unlink(clean_me)
            except:
                pass
           
jdwp = Extension(
	'andbug.jdwp', ['lib/jdwp/jdwp.c', 'lib/jdwp/wire.c']
)

setup(
	name = 'andbug',
	version = '0.1',
	description = 'The AndBug scriptable Android debugger',
	author = 'Scott Dunlop',
	author_email = 'swdunlop@gmail.com',
	package_dir = {
		'andbug' : 'lib/andbug',
		'andbug.cmd' : 'lib/andbug/cmd'
	},
	packages = ['andbug', 'andbug.cmd'],
	ext_modules = [jdwp],
	cmdclass = { 
		'test' : TestCommand, 
		'clean' : CleanCommand 
	},
    scripts = ['andbug']
)
