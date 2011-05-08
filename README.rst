=======================================
AndBug -- A Scriptable Android Debugger
=======================================

AndBug is a debugger targeting the Android platform's Dalvik virtual machine intended for reverse engineers and developers.  It uses the same interfaces as Android's Eclipse debugging plugin, the Java Debug Wire Protocol (JDWP) and Dalvik Debug Monitor (DDM) to permit users to hook Dalvik methods, examine process state, and even perform changes.

Unlike Google's own Android Software Development Kit debugging tools, AndBug does not require or expect source code.  It does, however, require that you have some level of comfort with Python, as it uses a concept of scripted breakpoints, called "hooks", for most nontrivial tasks.  (If you just want to dump loaded classes, methods, or threads, there are example scripts for that.)

At IOActive, I use AndBug and tools like it every day to study the Android platform and understand customer applications.  It is a living tool which has lead to discovering a number of vulnerabilities by chasing process flow across the system and exposing how weak the Android process isolation model really is, once you get under the hood.  I hope you enjoy it, and welcome any improvements or suggestions.

-- Scott Dunlop <swdunlop@gmail.com>

Installation
------------

AndBug is very much a program in flux, as I seperate one-off scripts I have written at IOActive for various tasks from customer and IOActive-proprietary contexts.  I do not recommend installation at this time, as you will want to update it frequently afterwards.  AndBug runs very nicely from its own source directory with very little setup.

1. Install the Android Software Development Kit from https://developer.android.com/sdk/index.html

2. Ensure the Android Debugging Bridge is in your $PATH and usable. ::
   
   adb devices

3. Ensure you have a good Python and GNU toolchain for your platform.  You will need GCC, and Make.  You may also want Pyrex, if you want to make changes at the primitive layer.

4. Pull the latest AndBug code from https://github.com/swdunlop/AndBug.git ::

   git clone https://github.com/swdunlop/AndBug.git

5. Build using Make ::
   
   make

Examples
--------

Examples can be found in the sample directory, but the easiest way to find prepackaged functionality in AndBug is using the "andbug" command directly. ::
    
   ./andbug

License
-------

Copyright 2011, Scott W. Dunlop <swdunlop@gmail.com> All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY SCOTT DUNLOP "AS IS" AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL SCOTT DUNLOP OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

