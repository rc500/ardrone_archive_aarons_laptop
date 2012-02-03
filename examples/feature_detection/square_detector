# basic edge detection code

from PIL import Image
import ImageFilter
import cv
import numpy as np
import sys

#load greyscale image
img = cv.LoadImageM("s2.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
#load colour image for displaying
im = cv.LoadImageM("s2.jpg");

#canny edge detector

edges= cv.CreateImage(cv.GetSize(img), 8, 1)
cv.Canny(img,edges, 50, 400.0)

#low-pass filter the image
cv.Smooth(edges, edges, cv.CV_GAUSSIAN,25)

#Determine strong corners in the image   

coord=[];

eig_image = cv.CreateImage(cv.GetSize(img), cv.IPL_DEPTH_32F, 1)
temp_image = cv.CreateImage(cv.GetSize(img), cv.IPL_DEPTH_32F, 1)
for (x,y) in cv.GoodFeaturesToTrack(edges, eig_image, temp_image, 100, 0.04, 1.0, useHarris = True):
  #print "good feature at", x,y
  coord.append((x,y));
  cv.Circle(im,(int(x),int(y)) ,3,cv.RGB(0, 0,0))



coord_new=[];

mn=min(coord);
mx=max(coord)
coord_new.append(mn);
coord_new.append((mn[0],mx[1]));
coord_new.append(mx);
coord_new.append((mx[0],mn[1]));

#create space to store the cvseq sequence seq containing teh contours
storage = cv.CreateMemStorage(0)

#find countours returns a sequence of countours so we need to go through all of them
#to find rectangles. see http://opencv.willowgarage.com/wiki/PythonInterface
#for details

#find all contours and draw inner ones in green, outter in blues
seq=cv.FindContours(edges, storage,cv.CV_RETR_LIST,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))
cv.DrawContours(im, seq, (255,0,0), (0,255,0), 20,1)

#find external contours
seq_ext=cv.FindContours(edges, storage,cv.CV_RETR_EXTERNAL,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))

while seq:
  #do not take into account external countours
  if not(list(seq)==list(seq_ext)):
   polygon=cv.ApproxPoly(list(seq), storage,cv.CV_POLY_APPROX_DP,0,0)
   cv.PolyLine(im,[polygon], True, (0,255,0),2, cv.CV_AA, 0)
  else:
    seq_ext=seq_ext.h_next()   
  #h_next: points to sequences om the same level
  seq=seq.h_next()





cv.NamedWindow("test1",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test1", im)

##cv.NamedWindow("test2",cv.CV_WINDOW_AUTOSIZE)
##cv.ShowImage("test2", edges)
cv.WaitKey(0) 




