# basic edge detection code

from PIL import Image
import ImageFilter
import cv
import numpy as np
import sys

img = Image.open("frame.jpg")

im.show()

#a=ImageFilter.Kernel((5,5),[-0.03,-0.4,1,0.04,0.03,-0.03,-0.4,1,0.04,0.03,-0.03,-0.4,1,0.04,0.03,-0.03,-0.4,1,0.04,0.03,-0.03,-0.4,1,0.04,0.03])
#im1 = img.filter(a)
#im1.show()

##im = cv.LoadImageM("frame.jpg")
##
##dst = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_16S, 3)
##laplace = cv.Laplace(im, dst)
##
##
##cv.NamedWindow("test1")
##cv.ShowImage("test1", im)
##cv.WaitKey(0) 
##



