#SURF descriptor test

from PIL import Image
import ImageFilter
import cv
import numpy as np
import sys

#load greyscale image
img = cv.LoadImageM("s2.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
#load colour image for displaying
im = cv.LoadImageM("s2.jpg");

edges= cv.CreateImage(cv.GetSize(img), 8, 1)
cv.Canny(img,edges, 50, 400.0)

#low-pass filter the image
cv.Smooth(edges, edges, cv.CV_GAUSSIAN,19)

(keypoints, descriptors) = cv.ExtractSURF(edges, None, cv.CreateMemStorage(), (0, 500, 3,4))

for ((x, y), laplacian, size, dir, hessian) in keypoints:
      #print "x=%d y=%d laplacian=%d size=%d dir=%f hessian=%f" % (x, y, laplacian, size, dir, hessian)
      cv.Circle(im,(int(x),int(y)) ,3,cv.RGB(0, 255, 0))

cv.NamedWindow("test1",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test1", im)

cv.NamedWindow("test2",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test2", edges)

cv.WaitKey(0) 
      
