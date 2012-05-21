# Testing the optical flow OpenCV function. 

from PIL import Image
import ImageFilter
import cv
import numpy as np
import sys

#load greyscale image
img1 = cv.LoadImageM("s1.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
#load colour image for displaying
im1 = cv.LoadImageM("s1.jpg");

#load greyscale image
img2 = cv.LoadImageM("s2.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
#load colour image for displaying
im2 = cv.LoadImageM("s2.jpg");


vel_size = (img1.width- 8, img1.height - 8)
#create storage space for the x and y velocity images
velx = cv.CreateImage(vel_size, cv.IPL_DEPTH_32F, 1)
vely = cv.CreateImage(vel_size, cv.IPL_DEPTH_32F, 1)
#calculate optical flow
cv.CalcOpticalFlowBM(img1,img2, (8,8), (1,1), (8,8), 0, velx, vely)

#printing out the values of velx for testing, commented out-
#code runs too slowly otherwise
##for i in range(312) :
##    for j in range(232):
##        print velx[i,j]
    
    


cv.NamedWindow("test1",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test1", velx)

cv.NamedWindow("test2",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test2", vely)
cv.WaitKey(0) 




