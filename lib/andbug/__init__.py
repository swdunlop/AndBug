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

'''
AndBug is a debugger targeting the Android platform's Dalvik virtual machine
intended for reverse engineers and developers. It uses the same interfaces 
as Android's Eclipse debugging plugin, the Java Debug Wire Protocol (JDWP) 
and Dalvik Debug Monitor (DDM) to permit users to hook Dalvik methods, 
examine process state, and even perform changes.
'''

import andbug.jdwp
import andbug.proto
import andbug.log
import andbug.command
import andbug.vm
import andbug.screed
from andbug.errors import (
    UserError, OptionError, ConfigError, DependencyError
)

## andbug.command -- utilities for writing andbug commands
from andbug.command import action

#TODO: andbug.options
#TODO: andbug.forward

## andbug.vm -- abstraction of the virtual machine model
from andbug.vm import (
    Element, Session, Frame, Array, Object, String, Method, RefType, Slot, 
    Thread, Hook, Location, Class, connect
)
