# Script to test various feature detector functions available in OpenCV

from PIL import Image
import ImageFilter
import cv
import numpy as np
import sys

#load greyscale image
img1 = cv.LoadImageM("bx5.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
#load colour image for displaying
im1 = cv.LoadImageM("bx5.jpg");

#load greyscale image
img2 = cv.LoadImageM("s2.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
#load colour image for displaying
im2 = cv.LoadImageM("s2.jpg");

#select the type of detector to be used
feature= 's_c';

if feature=='c':
    #canny edge detector

    edges= cv.CreateImage(cv.GetSize(img), 8, 1)
    cv.Canny(img,edges, 50, 400.0)

    #low-pass filter the image
    cv.Smooth(img, img, cv.CV_GAUSSIAN,15)
    
if feature=='c_m':
    #creates map for corner detection

    corners = cv.CreateImage(cv.GetSize(img1), cv.IPL_DEPTH_32F, 1)
    cv.PreCornerDetect(img1, corners, apertureSize=3)

    for y in range(0, im1.height):
     for x in range(0, im1.width):
      crnr = cv.Get2D(corners, y, x) # get the x,y value
      # check the corner detector response
      if crnr[0] > 10e-06:
       # draw a small circle on the original image
       cv.Circle(im1,(x,y),2,cv.RGB(0,0 ,255))

if feature== 'h':
    # harris edge detector
    harris_dst = cv.CreateMat(img1.height,img1.width, cv.CV_32FC1)
    cv.CornerHarris(img1, harris_dst,3)

    for y in range(0, im1.height):
     for x in range(0, im1.width):
      harris = cv.Get2D(harris_dst, y, x) # get the x,y value
      # check the corner detector response
      if harris[0] > 10e-06:
       # draw a small circle on the original image
       cv.Circle(im1,(x,y),2,cv.RGB(255, 0, 0))

if feature=='s_c':
    #Determine strong corners in the image   

    eig_image = cv.CreateImage(cv.GetSize(img1), cv.IPL_DEPTH_32F, 1)
    temp_image = cv.CreateImage(cv.GetSize(img1), cv.IPL_DEPTH_32F, 1)
    for (x,y) in cv.GoodFeaturesToTrack(img1, eig_image, temp_image, 100, 0.04, 1.0, useHarris = True):
      #print "good feature at", x,y
      #put green circles around detected harris corners
      cv.Circle(im1,(int(x),int(y)) ,3,cv.RGB(255, 255, 0))

if feature=='surf':
     #SURF implementation for both images
     (keypoints1, descriptors1) = cv.ExtractSURF(img1, None, cv.CreateMemStorage(), (0, 3000, 3,1))
     (keypoints2, descriptors2) = cv.ExtractSURF(img2, None, cv.CreateMemStorage(), (0, 3000, 3,1))


     for ((x, y), laplacian, size, dir, hessian) in keypoints1:
        cv.Circle(im1,(int(x),int(y)) ,3,cv.RGB(255, 255, 0))

     for ((x, y), laplacian, size, dir, hessian) in keypoints2:
        cv.Circle(im2,(int(x),int(y)) ,3,cv.RGB(255, 255, 0))        
    

#display image 1
cv.NamedWindow("test1",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test1", im1)

#display image 2
cv.NamedWindow("test2",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test2", im2)
cv.WaitKey(0) 




