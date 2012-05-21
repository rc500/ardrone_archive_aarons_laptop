from PIL import Image
import ImageFilter
import cv
import numpy as np
import sys

#load greyscale image
img = cv.LoadImageM("bx5.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
#load colour image for displaying
im = cv.LoadImageM("bx5.jpg");

edges= cv.CreateImage(cv.GetSize(img), 8, 1);

cv.Canny(img,edges, 50, 200.0);

#smooth resulting image of edges by a Gaussian of kernel size 25
cv.Smooth(edges, edges, cv.CV_GAUSSIAN,25)

cv.NamedWindow("test1",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test1", edges)
cv.WaitKey(0) 


