import os
import signal
import sys
import socket, time
import cv
from PIL import Image
from numpy import array
import ImageFilter

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

                #canny edge detector
                edges= cv.CreateImage(cv.GetSize(img), 8, 1)
                cv.Canny(img,edges, 50, 400.0)

                #low-pass filter the image
                cv.Smooth(edges, edges, cv.CV_GAUSSIAN,25)

                #create space to store the cvseq sequence seq containing the contours
                storage = cv.CreateMemStorage(0)

                #find countours returns a sequence of countours so we need to go through all of them
                #to find rectangles. see http://opencv.willowgarage.com/wiki/PythonInterface
                #for details

                #find all contours and draw inner ones in green, outter in blue
                seq=cv.FindContours(edges, storage,cv.CV_RETR_LIST,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))
                cv.DrawContours(im, seq, (255,0,0), (0,255,0), 20,1)

                #find external contours
                seq_ext=cv.FindContours(edges, storage,cv.CV_RETR_EXTERNAL,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))

                # go through the sequence for each contour
                while seq:
                  #do not take into account external countours
                  if not(list(seq)==list(seq_ext)):
                   # approximate the inner conour by polygons       
                   polygon=cv.ApproxPoly(list(seq), storage,cv.CV_POLY_APPROX_DP,0,0)
                   #then fit a square to it, function below returns (x,y,width, height)
                   #where (x,y) the top leftmost of te vertices
                   sqr=cv.BoundingRect(polygon,0)
                   #Only keep rectangles big enough to be of interest and are concave
                   if (not cv.CheckContourConvexity(polygon)) & (float(sqr[2]*sqr[3])/(edges.height*edges.width)>0.1):
                    #draw approximated polygon (thicker green line)
                    cv.PolyLine(im,[polygon], True, (0,0,255),2, cv.CV_AA, 0)
                    #draw fitted square (magenta line)
                    cv.Rectangle(im,(sqr[0],sqr[1]),(sqr[0]+sqr[2],sqr[1]+sqr[3]),(255,0,255),1,8,0)
                  else:
                    #move on to the next outter contour      
                    seq_ext=seq_ext.h_next()   
                  #h_next: points to sequences on the same level
                  seq=seq.h_next()
  
                return im

#Create a class that deals with interesting detected data
class objectAvoider(object):

        def _init_(self):
                pass
        def dodge(self,sqr):

          #if the square becomes too big, i.e. we get too close
          if (sqr[2]>225) or (sqr[3]>150):
              return 1 
                
                
 

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
