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

'implementation of recent allocations commands'

import andbug.command, andbug.screed, andbug.options
from Queue import Queue

from andbug.vm import RequestError

@andbug.command.action(
    '', name='version', aliases=('v',), shell=False,
)
def version(ctxt):
    'Send version request.'

    conn = ctxt.sess.conn
    buf = conn.buffer()

    # 0x0101 = {1, 1} VirtualMachine.Version
    code, ret = conn.request(0x0101, buf.data())
    if code != 0:
        raise RequestError(code)

    # string    description	Text information on the VM version
    # int	jdwpMajor	Major JDWP Version number
    # int	jdwpMinor	Minor JDWP Version number
    # string	vmVersion	Target VM JRE version, as in the java.version property
    # string	vmName	        Target VM name, as in the java.vm.name property

    rets = ret.unpack("$ii$$")
    (description, jdwpMajor, jdwpMinor, vmVersion, vmName) = rets

    with andbug.screed.section('Version'):
        with andbug.screed.section('Text information on the VM version'):
            andbug.screed.item("%s" % description)
        with andbug.screed.section('JDWP Version number'):
            andbug.screed.item(str((jdwpMajor, jdwpMinor)))
        with andbug.screed.section('Target VM'):
            andbug.screed.item(str((vmVersion, vmName)))
