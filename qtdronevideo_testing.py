import os
import signal
import sys
import socket, time
import cv
from PIL import Image
from numpy import array

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import qt modules (platform independant)
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')
QtNetwork = qt.import_module('QtNetwork')

# Import other objects
from ardrone.core.controlloop import ControlLoop
from ardrone.platform import qt as platform
import ardrone.core.videopacket as videopacket
#from ardrone.aruco import detect_markers

class imageProcessor(object):
        def __init__(self):
                pass

        def detect_markers (self, frame):
                
                #convert prep
                cv.SaveImage("frame.png", frame)

                #load greyscale image
                img = cv.LoadImageM("frame.png",cv.CV_LOAD_IMAGE_GRAYSCALE)
                #load colour image for displaying
                im = cv.LoadImageM("frame.png");

                cv.Smooth(img, img, cv.CV_GAUSSIAN,15)

                # harris edge detector
                harris_dst = cv.CreateMat(img.height,img.width, cv.CV_32FC1)
                cv.CornerHarris(img, harris_dst,3)

##                for y in range(0, im.height):
##                  for x in range(0, im.width):
##                     harris = cv.Get2D(harris_dst, y, x) # get the x,y value
##                     # check the corner detector response
##                     if harris[0] > 10e-06:
##                     # draw a small circle on the original image
##                        cv.Circle(im,(x,y),2,cv.RGB(255, 0, 0))

               #Determine strong corners in the image   
                eig_image = cv.CreateImage(cv.GetSize(img), cv.IPL_DEPTH_32F, 1)
                temp_image = cv.CreateImage(cv.GetSize(img), cv.IPL_DEPTH_32F, 1)
                for (x,y) in cv.GoodFeaturesToTrack(img, eig_image, temp_image, 100, 0.04, 1.0, useHarris = True):
                   #put green circles around detected harris corners
                   cv.Circle(im,(int(x),int(y)) ,3,cv.RGB(255, 255, 0))
                return im   
 

class imageViewer(object):

        win_title = "Drone Video Feed"

        def __init__(self):
                # Create a QtCoreApplication loop (NB remember to use QApplication instead if wanting GUI features)
                self.app = QtCore.QCoreApplication(sys.argv)

                # Wire up Ctrl-C to call QApplication.quit()
                signal.signal(signal.SIGINT, lambda *args: self.app.quit())

                # Initialise the drone control loop and attempt to open a connection.
                connection = platform.Connection()
                self._control = ControlLoop(connection, video_cb=None, navdata_cb=None)

                # Create a window in which to place frames
                cv.NamedWindow(self.win_title, cv.CV_WINDOW_AUTOSIZE) #probably no need to autosize

                # Set up a UDP listening socket on port 5562 which calls readData upon socket activity
                self.socket = QtNetwork.QUdpSocket()
                if not self.socket.bind(QtNetwork.QHostAddress.Any, 5562):
                        raise RuntimeError('Error binding to port: %s' % (self.socket.errorString()))
                self.socket.readyRead.connect(self.readData)

                # Create decoder object
                self._vid_decoder = videopacket.Decoder(self.showImage)
                
                # Create imageProcessor object
                self._img_processor = imageProcessor()
                
                # Start video on drone
                self._control.start_video()
                
        def run(self):
                self.app.exec_()
                
        def readData(self):
                """Called when there is some interesting data to read on the video socket."""
                while self.socket.hasPendingDatagrams():
                        sz = self.socket.pendingDatagramSize()
                        (data, host, port) = self.socket.readDatagram(sz)

                # Some hack to account for PySide vs. PyQt differences
                if qt.USES_PYSIDE:
                        data = data.data()
                
                # Decode video data and pass result to showImage
                self._vid_decoder.decode(data)
                        
        def showImage(self, data):
                """
                Displays argument image in window using openCV.
                data argument must be a string containing a 16 bit unsigned RGB image (RGB16 == RGB565).
                """

                # Create OpenCV header and read in drone video data as RGB565
                iplimage = cv.CreateImageHeader((320,240), cv.IPL_DEPTH_8U, 2)          
                cv.SetData(iplimage, data)
                
                # Convert image to RGB888 which is more OpenCV friendly
                RGBimage = cv.CreateImage((320,240), cv.IPL_DEPTH_8U, 3)
                cv.CvtColor(iplimage, RGBimage, cv.CV_BGR5652BGR)
                
                # Add labels for any markers present
                RGBimage = self._img_processor.detect_markers(RGBimage)
                
                # Show image
                cv.ShowImage(self.win_title, RGBimage)
                                
if (__name__ == '__main__'):
  image_app = imageViewer()
  image_app.run()
