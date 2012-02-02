# basic edge detection code

from PIL import Image
import ImageFilter
import cv
import numpy as np
import sys
import re

#load greyscale image
img1 = cv.LoadImageM("s1.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
#load colour image for displaying
im1 = cv.LoadImageM("s1.jpg");

#load greyscale image
img2 = cv.LoadImageM("s2.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
#load colour image for displaying
im2 = cv.LoadImageM("s2.jpg");


#SURF implementation
(keypoints1, descriptors1) = cv.ExtractSURF(img1, None, cv.CreateMemStorage(), (0, 3000, 3,1))
(keypoints2, descriptors2) = cv.ExtractSURF(img2, None, cv.CreateMemStorage(), (0, 3000, 3,1))

s=0;
for ((x1, y1), laplacian1, size1, dir1, hessian1) in keypoints1:
  if laplacian1==1:
      cv.Circle(im1,(int(x1),int(y1)) ,3,cv.RGB(255, 255, 0))
      print '1:',(x1,y1),s
  elif laplacian1==-1:
      cv.Circle(im1,(int(x1),int(y1)) ,3,cv.RGB(255, 0, 0))
  else:
      cv.Circle(im1,(int(x1),int(y1)) ,3,cv.RGB(0, 255, 0))
  s=s+1;    

s2=0;
for ((x2, y2), laplacian2, size2, dir2, hessian2) in keypoints2:
  if laplacian2==1:
      cv.Circle(im2,(int(x2),int(y2)) ,3,cv.RGB(255, 255, 0))
      print '2:',(x2,y2),s2
  elif laplacian2==-1:
      cv.Circle(im2,(int(x2),int(y2)) ,3,cv.RGB(255, 0, 0))
  else:
      cv.Circle(im2,(int(x2),int(y2)) ,3,cv.RGB(0, 255, 0))
  s2=s2+1;    
  
##for i in range(len(keypoints1)):
##   for j in range(len(keypoints2)):
####        if keypoints1[i][1]==keypoints2[j][1]:
####            #print i,j, keypoints1[i][1]
##        if descriptors2[j]==descriptors1[i]:
##            print 'a'

         
            



##for i in range(len(descriptors1)):

##    for j in range(len(descriptors2)):
##        if descriptors1[i]==descriptors2[j]:
##         
            
           




cv.NamedWindow("test1",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test1", im1)

cv.NamedWindow("test2",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test2", im2)
cv.WaitKey(0) 




