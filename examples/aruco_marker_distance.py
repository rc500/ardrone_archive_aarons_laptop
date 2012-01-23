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
import cv

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

  cv.NamedWindow("test",cv.CV_WINDOW_AUTOSIZE)
  
  # This is probably the simplest possible example.
  im = Image.open(sys.argv[1]).convert('RGB')

  CV_image = cv.LoadImage(sys.argv[1])
  
  #arr = array(im)
  for m in detect_markers(im):
	coord = (m.centroid_x(), m.centroid_y())
	print(coord)
	cv.Line(CV_image,(0,0),coord,cv.Scalar(1,1,1))

  cv.ShowImage("test",CV_image)


if __name__ == '__main__':
  main()
