"""
``aruco_marker_distance.py``: using the aruco bindings
--------------------------------------

This example program takes one command-line argument: the input image to
load which contains aruco markers. The centroid of these markers are then
output to terminal.
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
  if len(sys.argv) < 2:
    print('usage: aruco.py input.png')
    sys.exit(1)

  # This is probably the simplest possible example.
  im = Image.open(sys.argv[1]).convert('RGB')
  #arr = array(im)
  for m in detect_markers(im):
	centroid = m.centroid()
	print(centroid)

if __name__ == '__main__':
  main()
