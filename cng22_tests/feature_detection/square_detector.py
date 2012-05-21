# basic edge detection code

from PIL import Image
import ImageFilter
import cv
import numpy as np
import sys
import math

#load greyscale image
img = cv.LoadImage("bx5.jpg",cv.CV_LOAD_IMAGE_GRAYSCALE)
#load colour image for displaying
im = cv.LoadImage("bx5.jpg");

#canny edge detector
edges= cv.CreateImage(cv.GetSize(img), 8, 1)
cv.Canny(img,edges, 50, 400.0)

#low-pass filter the image
cv.Smooth(edges, edges, cv.CV_GAUSSIAN,25)

#create space to store the cvseq sequence seq containing teh contours
storage = cv.CreateMemStorage(0)

#find countours returns a sequence of countours so we need to go through all of them
#to find rectangles. see http://opencv.willowgarage.com/wiki/PythonInterface
#for details

#find all contours and draw inner ones in green, outter in blues
seq=cv.FindContours(edges, storage,cv.CV_RETR_LIST,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))
cv.DrawContours(im, seq, (255,0,0), (0,255,0), 20,2)

#find external contours
seq_ext=cv.FindContours(edges, storage,cv.CV_RETR_EXTERNAL,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))

while seq:
  #do not take into account external countours
  if not(list(seq)==list(seq_ext)):
   perim= cv.ArcLength(seq) #contour perimeter
   area=cv.ContourArea(seq) #contour area
   polygon=cv.ApproxPoly(list(seq), storage,cv.CV_POLY_APPROX_DP,perim*0.02,0)
   sqr=cv.BoundingRect(polygon,0)
   #Only keep rectangles big enough to be of interest,
   #that have an appropriate width/height ratio
   
   #and whose area is close enogh to that of the approximated rectangle
   if  (float(sqr[2]*sqr[3])/(edges.height*edges.width)>0.1) & (abs(sqr[2]-sqr[3])<((sqr[2]+sqr[3])/4))& (area/float(sqr[2]*sqr[3])>0.7): 
    #cv.PolyLine(im,[polygon], True, (0,255,0),2, cv.CV_AA, 0)
    cv.Rectangle(im,(sqr[0],sqr[1]),(sqr[0]+sqr[2],sqr[1]+sqr[3]),(255,0,255),2,8,0)
    print sqr[2],sqr[3], len(seq), 
    #area_small=cv.ContourArea(seq, (0, ))
    #print area_small
    sub=cv.GetSubRect(im, (sqr[0], sqr[1], int(round(sqr[2]/2)), int(round(sqr[3]))))
    subim = cv.CreateImage(cv.GetSize(sub), 8, 3)
    cont_points=list(seq)
    r=cv.Get2D(im,int(round(img.width/2)),int(round(img.height/2)) )[2]
    g=cv.Get2D(im,int(round(img.width/2)),int(round(img.height/2)))[1]
    b=cv.Get2D(im,int(round(img.width/2)),int(round(img.height/2)))[0]

    subim=sub
    a=list(seq)
    print 'dim' ,(sqr[0]+sqr[2],sqr[1]), max(a)

    
    
    
    

    
  else:
    seq_ext=seq_ext.h_next()   
  #h_next: points to sequences om the same level
  seq=seq.h_next()





cv.NamedWindow("test1",cv.CV_WINDOW_AUTOSIZE)
cv.ShowImage("test1", im)
#cv.ShowImage("te1", subim)


##cv.NamedWindow("test2",cv.CV_WINDOW_AUTOSIZE)
##cv.ShowImage("test2", edges)
cv.WaitKey(0) 




