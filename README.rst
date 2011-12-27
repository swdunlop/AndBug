=======================================
AndBug -- A Scriptable Android Debugger
=======================================

AndBug is a debugger targeting the Android platform's Dalvik virtual machine intended for reverse engineers and developers.  It uses the same interfaces as Android's Eclipse debugging plugin, the Java Debug Wire Protocol (JDWP) and Dalvik Debug Monitor (DDM) to permit users to hook Dalvik methods, examine process state, and even perform changes.

Unlike Google's own Android Software Development Kit debugging tools, AndBug does not require or expect source code.  It does, however, require that you have some level of comfort with Python, as it uses a concept of scripted breakpoints, called "hooks", for most nontrivial tasks.  (If you just want to dump loaded classes, methods, or threads, there are example scripts for that.)

-- Scott Dunlop <swdunlop@gmail.com>

Installation
------------

AndBug is very much a program in flux, as I seperate one-off scripts I have written at IOActive for various tasks from customer and IOActive-proprietary contexts.  I do not recommend installation at this time, as you will want to update it frequently afterwards.  AndBug runs very nicely from its own source directory with very little setup.

1. Install the Android Software Development Kit from https://developer.android.com/sdk/index.html

2. Ensure the Android Debugging Bridge is in your $PATH and usable. ::
   
   which adb
   adb devices

3. Ensure you have a good Python and GNU toolchain for your platform.  You will need GCC, and Make.  You may also want Pyrex, if you want to make changes at the primitive layer.

4. Pull the latest AndBug code from https://github.com/swdunlop/AndBug.git ::

   git clone https://github.com/swdunlop/AndBug.git

5. Build using Make ::
   
   make

6. Adjust $PYTHONPATH ::
   
   export PYTHONPATH=`pwd`/lib

Examples
--------

Examples can be found in the sample directory, but the easiest way to find prepackaged functionality in AndBug is using the "andbug" command directly. ::
    
   ./andbug

This command does not currently have the intelligence to automatically detect when it is running from the source directory and update the PYTHONPATH on the fly to match.  You will want to make sure that PYTHONPATH includes your andbug/lib directory.

Common Problems
---------------

Q: I get "Permission Denied" when trying to use AndBug, but "adb shell" works.

A: Your adbd is probably running as another user, blocking the effective use of ADB forward.  Use "adb kill-server" then "adb start-server" with the correct effective user.

Q: I get "Shell Exception" when trying to use AndBug.

A: Verify that your ADB setup is working using "adb devices" -- AndBug relies on ADB for a JDWP transport.

Q: Does AndBug work on Windows?

A: I think so; but since AndBug is unsupported software, you may experience less hand holding than Windows users are accustomed to.  Patches are welcome.

Q: Does AndBug work on Mac OS X?

A: Yes, but see the snarkiness about Windows users.  You didn't find this in an app store..

Q: Navi gives me an RequestError 13.

A: You have resumed the process; Navi can only safely interact with suspended processes.  Use "suspend" again.

Q: I get "EOF in read" when sending a commmand.

A: Ensure that no other debuggers are connected, such as DDMS.

License
-------

Copyright 2011, IOActive All rights reserved.

AndBug is free software: you can redistribute it and/or modify it under 
the terms of version 3 of the GNU Lesser General Public License as 
published by the Free Software Foundation.

AndBug is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS 
FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for 
more details.

You should have received a copy of the GNU Lesser General Public License
along with AndBug.  If not, see <http://www.gnu.org/licenses/>.
