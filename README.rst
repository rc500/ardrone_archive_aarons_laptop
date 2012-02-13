Drone controller
================

This is a selection of Python software for controlling the `AR.Drone Parrot
<http://ardrone.parrot.com/parrot-ar-drone/uk/>`_. It is a work in progress and
is being developed as part of a Masters Degree project at the Univeristy of
Cambridge.

Building the native libraries
-----------------------------

Native Win32 DLLs are provided in the ardrone/native/lib directory but native
Linux libaries need to be built via the ``compile-native-linux.sh`` schell
script. In addition, a corresponding ``compile-native-mingw-win32.sh`` script
is provided for those cross-compiling the Windows DLLs using MinGW under Linux.

When cross-compiling for Windows, the OpenCV source is expected to reside in
the ``native/win32-third-party/opencv`` directory relative to the
``compile-native-mingw-win32.sh`` script.

Building the documentation
--------------------------

A simple Makefile is provided for building the documentation, such as it is.

Copying
-------

For any files not under 'native':

    Copyright 2011, 2012 the Contributors listed in CONTRIBUTORS.txt.

       Licensed under the Apache License, Version 2.0 (the "License");
       you may not use this file except in compliance with the License.
       You may obtain a copy of the License at

           http://www.apache.org/licenses/LICENSE-2.0

       Unless required by applicable law or agreed to in writing, software
       distributed under the License is distributed on an "AS IS" BASIS,
       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
       See the License for the specific language governing permissions and
       limitations under the License.

Files under the 'native' directory include Derivative Works from the AR Drone
SDK and Aruco SDK which may carry license terms more restrictive than the
above.
