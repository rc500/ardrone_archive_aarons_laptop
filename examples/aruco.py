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

# Check the command-line arcuments.
if len(sys.argv) < 3:
  print('usage: aruco.py input.png output.png')
  sys.exit(1)

# This is probably the simplest possible example.
arr = array(Image.open(sys.argv[1]).convert('RGB'))
[m.draw(arr) for m in detect_markers(arr)]
Image.fromarray(arr).save(sys.argv[2], 'PNG')
