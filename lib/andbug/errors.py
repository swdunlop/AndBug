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

import sys

class UserError(Exception):
    'indicates an error in how AndBug was used'
    pass

class OptionError(UserError):
    'indicates an error parsing an option supplied to a command'
    pass

class ConfigError(UserError):
    'indicates an error in the configuration of AndBug'
    pass

class DependencyError(UserError):
    'indicates that an optional dependency was not found'
    pass

class VoidError(UserError):
    'indicates a process returned a nil object'

def perr(*args):
    print >>sys.stderr, ' '.join(map(str, args))

