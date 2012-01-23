"""
``aruco.py``: using the aruco bindings
--------------------------------------

This is a simple example program which takes two command-line arguments: the
input image to load which contains aruco markers and an output image filename
to write a copy of the input image with the detected marker positions drawn
into it.

"""
import logging
logging.basicConfig(level = logging.DEBUG)

import os
import sys
from numpy import array
from PIL import Image

# Where is this file?
this_dir = os.path.abspath(os.path.dirname(__file__))

# Insert a path to load modules from relative to this file
sys.path.insert(0, os.path.abspath(os.path.join(this_dir, '..')))

# Load the aruco module.
from ardrone.aruco import detect_markers

def main():
  """The main entry point of the program."""

  # Check the command-line arcuments.
  if len(sys.argv) < 3:
    print('usage: aruco.py input.png output.png')
    sys.exit(1)

  # This is probably the simplest possible example.
  im = Image.open(sys.argv[1]).convert('RGB')
  arr = array(im)
  [m.draw(arr) for m in detect_markers(im)]
  Image.fromarray(arr).save(sys.argv[2], 'PNG')

if __name__ == '__main__':
  main()
