# Testing the optical flow OpenCV function,
#info on how to use from http://nullege.com/codes/search/cv.CalcOpticalFlowBM

from PIL import Image
import ImageFilter
import cv
import numpy as np
import sys

#load greyscale image
img1 = cv.LoadImageM("t1.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
#load colour image for displaying
im1 = cv.LoadImageM("t1.jpg");

#load greyscale image
img2 = cv.LoadImageM("t2.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
#load colour image for displaying
im2 = cv.LoadImageM("t2.jpg");

a=img1

vel_size = (img1.width- 8, img1.height - 8)
#create storage space for the x and y velocity images
velx = cv.CreateImage(vel_size, cv.IPL_DEPTH_32F, 1)
vely = cv.CreateImage(vel_size, cv.IPL_DEPTH_32F, 1)
#calculate optical flow
cv.CalcOpticalFlowBM(img1,img2, (8,8), (1,1), (8,8), 0, velx, vely)


scribble = cv.CreateImage(cv.GetSize(im1), 8, 3)
print 'ok'
for y in range(0,228, 4):
    for x in range(0,308, 4):
        cv.Line(scribble, (x, y), (int(x+velx[y,x]), int(y + vely[y,x])), (0,255,0))
        print(x,y)
cv.Line(a, (640/5,0), (640/5,480), (255,0,0))
cv.Line(a, (0,360/5), (640,360/5), 255)


cv.NamedWindow("test",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test", scribble)

cv.NamedWindow("test1",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test1", velx)

cv.NamedWindow("test2",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test2", vely)
cv.WaitKey(0) 




