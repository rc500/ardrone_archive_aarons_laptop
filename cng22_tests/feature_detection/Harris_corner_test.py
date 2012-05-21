#test script to explore ho the Harris edge detector Opencv function works

import cv
img = cv.LoadImageM("s1.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
im = cv.LoadImageM("s1.jpg");

#create images to store image resuts used to calculate the corners
eig_image = cv.CreateImage(cv.GetSize(img), cv.IPL_DEPTH_32F, 1)
temp_image = cv.CreateImage(cv.GetSize(img), cv.IPL_DEPTH_32F, 1)

#iterate through the detected corners and display their (x,y) coordinates
for (x,y) in cv.GoodFeaturesToTrack(img, eig_image, temp_image, 2, 0.04, 1.0, useHarris = True):
  print "good feature at", x,y

      
