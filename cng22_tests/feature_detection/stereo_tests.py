# Stereo test, not working

from PIL import Image
import ImageFilter
import cv
import numpy as np
import sys

#stereo image 1
img1 = cv.LoadImageM("s1.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE);
#stereo image 2
img2 = cv.LoadImageM("s2.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE);

#cv.FindStereoCorrespondenceGC(img2, img1, dispLeft, dispRight, state,0)

cv.NamedWindow("test1",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test1", img1)

cv.NamedWindow("test2",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test2", img2)
cv.WaitKey(0) 
