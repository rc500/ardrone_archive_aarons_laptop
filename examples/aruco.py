import logging
logging.basicConfig(level = logging.DEBUG)

import os
import sys
from PIL import Image
import numpy as np

# Where is this file?
this_dir = os.path.abspath(os.path.dirname(__file__))

# Insert a path to load modules from relative to this file
sys.path.insert(0, os.path.abspath(os.path.join(this_dir, '..')))

# Load the ardrone modules
import ardrone.aruco as aruco

def main():
  if len(sys.argv) < 3:
    print('usage: aruco.py input.png output.png')
    return False

  arr = np.array(Image.open(sys.argv[1]).convert("RGB"))
  detector = aruco.MarkerDetector()
  markers = detector.detect(arr)
  for m in markers:
    m.draw(arr)
  Image.fromarray(arr).save(sys.argv[2], 'PNG')

  return True

if __name__ == '__main__':
  if not main():
    sys.exit(1)
