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

