import cv
img = cv.LoadImageM("lena1.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)

eig_image = cv.CreateImage(cv.GetSize(img), cv.IPL_DEPTH_32F, 1)
temp_image = cv.CreateImage(cv.GetSize(img), cv.IPL_DEPTH_32F, 1)
for (x,y) in cv.GoodFeaturesToTrack(img, eig_image, temp_image, 2, 0.04, 1.0, useHarris = True):
  print "good feature at", x,y

