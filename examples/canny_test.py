from PIL import Image
import ImageFilter
import cv
import numpy as np
import sys

#load greyscale image
img = cv.LoadImageM("frame2.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
#load colour image for displaying
im = cv.LoadImageM("frame2.jpg");

edges= cv.CreateImage(cv.GetSize(img), 8, 1);

cv.Canny(img,edges, 50, 200.0);

cv.NamedWindow("test1",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test1", edges)
cv.WaitKey(0) 
