#Code used for the final demonstration produced

import os
import signal
import sys
import socket, time
import cv
import json
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

"""A global socket object which can be used to send commands to the GUI program."""
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

"""A global sequence counter. The GUI uses this to determine if two commands
have been received in the wrong order: the command with the largest (latest)
sequence will always 'win'."""
seq_m = 0

def send_state(state):
  """Send the state dictionary to the drone GUI.

  state is a dictionary with (at least) the keys roll, pitch, yaw, gas,
  take_off, reset and hover. The first four are floating point values on the
  interval [-1,1] which specify the setting of the corresponding attitude
  angle/vertical speed. The last three are True or False to indicate if that
  virtual 'button' is pressed.

  """
  global seq_m, sock
  seq_m += 1
  HOST, PORT = ('127.0.0.1', 5560)
  #print('state is', json.dumps({'seq': seq_m, 'state': state}))
  sock.sendto(json.dumps({'seq': seq_m, 'state': state}), (HOST, PORT))

normal_state = {
      'roll': 0.0,
      'pitch': 0.0,
      'yaw': 0.0,
      'gas': 0.0,
      'take_off': False,
      'reset': False,
      'hover': True,
  }

turn_left_state = {
      'roll': 0.0,
      'pitch': 0.0,
      'yaw': -0.6,
      'gas': 0.0,
      'take_off': False,
      'reset': False,
      'hover': False,
}

turn_right_state = {
      'roll': 0.0,
      'pitch': 0.0,
      'yaw': 0.6,
      'gas': 0.0,
      'take_off': False,
      'reset': False,
      'hover': False,
}

slow_left_state = {
      'roll': 0.0,
      'pitch': 0.0,
      'yaw': -0.4,
      'gas': 0.0,
      'take_off': False,
      'reset': False,
      'hover': False,
}

slow_right_state = {
      'roll': 0.0,
      'pitch': 0.0,
      'yaw': 0.4,
      'gas': 0.0,
      'take_off': False,
      'reset': False,
      'hover': False,
}

move_forward_state = {
      'roll':0.0,
      'pitch': -0.06,
      'yaw': 0.0,
      'gas': 0.0,
      'take_off': False,
      'reset': False,
      'hover': False,
}

move_left_state = {
      'roll':-0.06,
      'pitch': 0.0,
      'yaw': 0.0,
      'gas': 0.0,
      'take_off': False,
      'reset': False,
      'hover': False,
}

move_right_state = {
      'roll':0.06,
      'pitch': 0.0,
      'yaw': 0.0,
      'gas': 0.0,
      'take_off': False,
      'reset': False,
      'hover': False,
}
    

#function to convert angles from gyro output to usable values
def convertAngle(angle):

  if angle<0:
    return (angle+360000.0)
  else:
    return angle
  

class navdataUpdate(object):

   def __init__(self,_im_proc):

    # Assign image processor pointer
    self._im_proc = _im_proc
    
    # Set up a UDP listening socket on port 5561 which calls readData upon socket activity
    self.data_socket = QtNetwork.QUdpSocket()
    if not self.data_socket.bind(QtNetwork.QHostAddress.Any, 5561):
            raise RuntimeError('Error binding to port: %s' % (self.data_socket.errorString()))
    self.data_socket.readyRead.connect(self.readNavigation_Data)
    
   def readNavigation_Data(self):
            """Called when there is some interesting data to read on the video socket."""
            while self.data_socket.hasPendingDatagrams():
                    sz = self.data_socket.pendingDatagramSize()
                    (data, host, port) = self.data_socket.readDatagram(sz)

            # Some hack to account for PySide vs. PyQt differences
            if qt.USES_PYSIDE:
                    data = data.data()
                    
            # Parse the packet
            packet = json.loads(data.decode())

            # Find the movement data we are looking for
            if 'type' in packet:
                if packet['type'] == 'demo':
                  #pass on yaw angle data to the image processor
                  #packet['psi'] is the yaw angle value
                  self._im_proc.yaw_angle = packet['psi']
                  



class imageProcessor(object):

        #variable that stores the yaw angle for a given point in time
        yaw_angle=0.0
        init_angle=0.0

        #counts if we are going one way or the other to determine the right
        #angle to check
        direction=-1

        #time a box was found
        box_time=0

        #time at which the turning (re-adjustment) state starts adjusting drone position/orientation
        detected_time=0
        
        #can we see a box in teh distance?
        box_in_distance=False

        #initialise the gyro drift to a value marking the first run
        drift=-1
        #time t0
        t_beg=0
        #yaw value at take-off
        y_beg=0.0

        #initialise a vector that will store the yaw angle at which landmarks were detected-used for mapping
        landmarks=[]
        
        #initialise the state
        state = 'take off'
        
        def __init__(self):

                #update the navigation data   
                self._navdata_update=navdataUpdate(self)
                      

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

                #find all contours and draw inner ones in green, outter in blues
                seq=cv.FindContours(edges, storage,cv.CV_RETR_LIST,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))
                cv.DrawContours(im, seq, (255,0,0), (0,255,0), 20,1)

                #find external contours
                seq_ext=cv.FindContours(edges, storage,cv.CV_RETR_EXTERNAL,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))

                while seq:
                  
                  #do not take into account external countours
                  if not(list(seq)==list(seq_ext)):
                    
                   perim= cv.ArcLength(seq) #contour perimeter
                   area=cv.ContourArea(seq) #contour area      
                   polygon=cv.ApproxPoly(list(seq), storage,cv.CV_POLY_APPROX_DP,perim*0.02,0)
                   sqr=cv.BoundingRect(polygon,0) #get square approximation for the contour;
                   # note: (sqr[0],sqr[1]) are the (x,y) coordinates of the top left corner of the square and sqr[2] its height and sqr[3] its width
                   
                   #check if there are any rectangles in the distance that have appropriate width/height ratio
                   #and area close enough to that of the approximated rectangle
                   #this is used to correct drone orientation when moving towards box
                   if (float(sqr[2]*sqr[3])/(edges.height*edges.width)>0.004)&(abs(sqr[2]-sqr[3])<((sqr[2]+sqr[3])/4))& (area/float(sqr[2]*sqr[3])>0.7):
                     self.box_in_distance = True
                     cv.PolyLine(im,[polygon], True, (0,255,255),2, cv.CV_AA, 0)
                     
                   
                   #Only keep rectangles big enough to be of interest,
                   #that have an appropriate width/height ratio
                   #and whose area is close enough to that of the approximated rectangle
                   if (float(sqr[2]*sqr[3])/(edges.height*edges.width)>0.06)&(abs(sqr[2]-sqr[3])<((sqr[2]+sqr[3])/4))& (area/float(sqr[2]*sqr[3])>0.7): 

                    #draw polygon and approximated rectangle 
                    cv.PolyLine(im,[polygon], True, (0,0,255),2, cv.CV_AA, 0)
                    cv.Rectangle(im,(sqr[0],sqr[1]),(sqr[0]+sqr[2],sqr[1]+sqr[3]),(255,0,255),1,8,0)

                    #check whether the box is too close and whether it could be green
                    if ((sqr[2]>100) or (sqr[3]>80)): 
                          pass

                            
                  else:
                    #move on to the next outter contour      
                    seq_ext=seq_ext.h_next()   
                  #h_next: points to sequences on the same level
                  seq=seq.h_next()
                  
                #check what state we are in and call the relevant function
                if self.state == 'take off':
                  self.take_off_state(frame)
                elif self.state == 'mapping':
                  self.mapping_state(frame)
                elif self.state == 'move':
                  self.move_state(frame)
                elif self.state == 'box found':
                  self.found_box_state(frame)
                elif self.state == 'yaw right':
                  self.yaw_right_state(frame)
                elif self.state == 'yaw left':
                   self.yaw_left_state(frame)
                elif self.state == 'turned':
                  self.turned_state(frame)
                elif self.state == 'adjusting_off_left':
                  self.adjusting_left_state(frame)                  
                elif self.state == 'adjusting_off_right':
                  self.adjusting_right_state(frame)                   
                  
                print self.state, ' state'

                #return teh image to be displayed 
                return im

                    
        def take_off_state(self,frame):

          #script to get an estimate of gyro drift after take off
          if self.drift == -1:
            t_beg = time.clock()
            self.drift = 0
            self.y_beg = convertAngle(self.yaw_angle)
          print self.yaw_angle  
          if time.clock()<0.5:
            send_state(normal_state)
          else:
            print 'done'
            y_end = convertAngle(self.yaw_angle)
            t_end = time.clock()
            self.drift=(abs(y_end-self.y_beg)/(t_end-self.t_beg))
            print self.drift ,'  time end', t_end, 'tbeg',self.t_beg, 'yend ',convertAngle(y_end),y_end, ' ybeg', convertAngle(self.y_beg)
            self.state = 'turned'
            return

        def mapping_state(self,frame):
        

          #load greyscale image
          img = cv.LoadImageM("frame.png",cv.CV_LOAD_IMAGE_GRAYSCALE)

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

          #find all contours and draw inner ones in green, outter in blues
          seq=cv.FindContours(edges, storage,cv.CV_RETR_LIST,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))

          #find external contours
          seq_ext=cv.FindContours(edges, storage,cv.CV_RETR_EXTERNAL,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))

          while seq:
            
            #do not take into account external countours
            if not(list(seq)==list(seq_ext)):
              
             perim= cv.ArcLength(seq) #contour perimeter
             area=cv.ContourArea(seq) #contour area      
             polygon=cv.ApproxPoly(list(seq), storage,cv.CV_POLY_APPROX_DP,perim*0.02,0)
             sqr=cv.BoundingRect(polygon,0) #get square approximation for the contour
             
             #check if there are any rectangles in the distance that have appropriate width/height ratio
             #and area close enough to that of the approximated rectangle
             #this is used to correct drone orientation when moving towards box
             if (float(sqr[2]*sqr[3])/(edges.height*edges.width)>0.004)&(abs(sqr[2]-sqr[3])<((sqr[2]+sqr[3])/4))& (area/float(sqr[2]*sqr[3])>0.7):
               #log the yaw angle of the deteced square (landmark)
               self.landmarks.append(abs(convertAngle(self.yaw_angle)-self.y_beg))
               print 'landmarks', self.landmarks
                      
            else:
              #move on to the next outter contour      
              seq_ext=seq_ext.h_next()   
            #h_next: points to sequences on the same level
            seq=seq.h_next()
            
          #if we have turned 360  or if we have been turning for too long we nee to stop  
          if (abs(convertAngle(self.yaw_angle)-self.y_beg)>10000.0)or time.clock()<8:
            send_state(slow_left_state)
            print abs(convertAngle(self.yaw_angle)-self.y_beg)
            return
          else:
            print abs(convertAngle(self.yaw_angle)-self.y_beg)
            self.state = 'turned'
            return
          

        def move_state(self,frame):

                send_state(move_forward_state)

                #load greyscale image
                img = cv.LoadImageM("frame.png",cv.CV_LOAD_IMAGE_GRAYSCALE)      

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

                #find all contours and draw inner ones in green, outter in blues
                seq=cv.FindContours(edges, storage,cv.CV_RETR_LIST,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))

                #find external contours
                seq_ext=cv.FindContours(edges, storage,cv.CV_RETR_EXTERNAL,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))

                while seq:
                  
                  #do not take into account external countours
                  if not(list(seq)==list(seq_ext)):
                    
                   perim= cv.ArcLength(seq) #contour perimeter
                   area=cv.ContourArea(seq) #contour area      
                   polygon=cv.ApproxPoly(list(seq), storage,cv.CV_POLY_APPROX_DP,perim*0.02,0)
                   sqr=cv.BoundingRect(polygon,0) #get square approximation for the contour
                   
                   #check if there are any rectangles in the distance that have appropriate width/height ratio
                   #and area close enough to that of the approximated rectangle
                   #this is used to correct drone orientation when moving towards box
                   if (float(sqr[2]*sqr[3])/(edges.height*edges.width)>0.004)&(abs(sqr[2]-sqr[3])<((sqr[2]+sqr[3])/4))& (area/float(sqr[2]*sqr[3])>0.7):
                     self.box_in_distance = True
      
                   #Only keep rectangles big enough to be of interest,
                   #that have an appropriate width/height ratio
                   #and whose area is close enough to that of the approximated rectangle
                   if (float(sqr[2]*sqr[3])/(edges.height*edges.width)>0.06)&(abs(sqr[2]-sqr[3])<((sqr[2]+sqr[3])/4))& (area/float(sqr[2]*sqr[3])>0.7): 


                    #check whether the box is too close and whether it could be green
                    if ((sqr[2]>100) or (sqr[3]>80)): 
 
                            print 'warning', sqr[2],sqr[3]
                            self.state =  'box found'
                            #record the time the box was found
                            self.box_time=time.clock()
                            return         
                  else:
                    #move on to the next outter contour      
                    seq_ext=seq_ext.h_next()   
                  #h_next: points to sequences on the same level
                  seq=seq.h_next()
                #if when we set out to move towards a box we haven't detected one let us know 
                if not self.box_in_distance:
                  print ' I think I am lost'
                 # if abs(convertAngle(self.yaw_angle)-convertAngle(self.y_beg))<160:
                  #    send_state(turn_right_state)
                  return
                  
                
                    
        def found_box_state(self,frame):

                  
        
                  #find whether we are going 'forward' or back depending on whether the
                  #angle magnitude is more or less that 180 degrees (values given by the drone
                  #are degrees*1000)
                  self.direction=cmp(convertAngle(self.yaw_angle), 180000.0)
                  #save the orientation the drone had when it found the box
                  self.init_angle=self.yaw_angle
                  #turn accordingly if box found
                  if self.direction==-1:
                   send_state(turn_right_state)
                   self.state = 'yaw right'
                   return    
                  if self.direction==1:
                   send_state(turn_left_state)
                   self.state = 'yaw left'
                   return

                  
        def yaw_right_state(self,frame):

                # provided we have detected a box and it has not rotated more than 180 degrees
                if(abs(-convertAngle(self.init_angle)+convertAngle(self.yaw_angle))<150000.0):
                     send_state(turn_right_state)
                     return
                    
                else:
                  #reset the timer
                  #self.box_time=0
                  self.state = 'turned'
                  return

        def yaw_left_state(self,frame):

              # provided we have detected a box and it has not rotated more than 180 degrees
              if(abs(convertAngle(self.init_angle)-convertAngle(self.yaw_angle))<150000.0 ):
                   send_state(turn_left_state)
                   return
                  
              else:
                #reset the timer
                #self.box_time=0
                self.state = 'turned'
                return

        def turned_state(self, frame):
          
                #load greyscale image
                img = cv.LoadImageM("frame.png",cv.CV_LOAD_IMAGE_GRAYSCALE)

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

                #find all contours and draw inner ones in green, outter in blues
                seq=cv.FindContours(edges, storage,cv.CV_RETR_LIST,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))

                #find external contours
                seq_ext=cv.FindContours(edges, storage,cv.CV_RETR_EXTERNAL,cv.CV_CHAIN_APPROX_SIMPLE,(0, 0))

                while seq:
                  
                  #do not take into account external countours
                  if not(list(seq)==list(seq_ext)):
                    
                   perim= cv.ArcLength(seq) #contour perimeter
                   area=cv.ContourArea(seq) #contour area      
                   polygon=cv.ApproxPoly(list(seq), storage,cv.CV_POLY_APPROX_DP,perim*0.02,0)
                   sqr=cv.BoundingRect(polygon,0) #get square approximation for the contour 
                   
                   #check if there are any rectangles in the distance that have appropriate width/height ratio
                   #and area close enough to that of the approximated rectangle
                   #this is used to correct drone orientation when moving towards box
                   if (float(sqr[2]*sqr[3])/(edges.height*edges.width)>0.004)&(abs(sqr[2]-sqr[3])<((sqr[2]+sqr[3])/4))& (area/float(sqr[2]*sqr[3])>0.7):
                     self.box_in_distance = True  
                     

                     if ((sqr[2]>100) or (sqr[3]>80)): 
 
                            print 'warning', sqr[2],sqr[3], area
                            #self.state =  'box found' -not needed
                            #record the time the box was found
                            self.box_time=time.clock()
                            #return

                     #get a list of the (x,y) points used to define the contour (in the case of a perfect rectangle those
                     #would be its vertices       
                     cont_points=list(seq)

                     #find the maximum (x,y) pair (see report for details)
                     max_xy=max(cont_points)

                     #find the minimum (x,y) pair (see report for details)
                     min_xy=min(cont_points)                     

                     #if the square if off-centre decide how to adjust the drone based on scene geometry   
                     if sqr[0]<0.2*edges.width or sqr[0]+sqr[2]>0.7*edges.width:
                       
                       #if the minimum y value corresponds to a point on the left of the image
                       if min_xy[0]< edges.width*0.25:
                         print 'move right and turn left', max_xy[0]

                         #save the time the box was detected and use to determine how much we turn
                         self.detected_time=time.clock()
                         self.state = 'adjusting_off_left'
                         return

                       #if the maximum y value corresponds to a point on the right of the image 
                       elif max_xy[0]> edges.width*0.75:
                         print 'move left and turn right', max_xy[0]

                         #save the time the box was detected and use to determine how much we turn
                         self.detected_time=time.clock()
                         self.state = 'adjusting_off_right'
                         return
                        
                     else:

                       self.state= 'move'
                       
               
                            
                  else:
                    #move on to the next outter contour      
                    seq_ext=seq_ext.h_next()   
                  #h_next: points to sequences on the same level
                  seq=seq.h_next()
                if not self.box_in_distance :
                  print ' I think i am lost, I can''t see any boxes'
                  if abs(convertAngle(self.yaw_angle)-convertAngle(self.y_beg))<160:
                      send_state(turn_right_state)
                      return

        #adjusting states are used to get teh drone facing the box again.
        #the drone moves riefly in the appropriate direction and then yaws briefly in teh appropriate direction
        def adjusting_left_state(self,frame):

            if (time.clock()-self.detected_time)<2:
              send_state(move_right_state)
              print 'moving right', self.detected_time-time.clock()
              
            elif(time.clock()-self.detected_time)<4:
              send_state(slow_left_state)
              print 'yawing left'   
              
            else:
              self.state='move'
              
              
              

        def adjusting_right_state(self,frame):  

            if (time.clock()-self.detected_time)<2:
              send_state(move_left_state)
              print 'moving left'
              
            elif(time.clock()-self.detected_time)<4:
              send_state(slow_right_state)
              print 'yawing right'
              
            else:
              self.state='move'                  
                     
                    
class imageViewer(object):

        win_title = "Drone Video Feed"

        def __init__(self):
                # Create a QtCoreApplication loop (NB remember to use QApplication instead if wanting GUI features)
                self.app = QtCore.QCoreApplication(sys.argv)

                # Wire up Ctrl-C to call QApplication.quit()
                signal.signal(signal.SIGINT, lambda *args: self.app.quit())

                # Initialise the drone control loop and attempt to open a connection.
                connection = platform.Connection()
                #self._control = ControlLoop(connection, video_cb=None, navdata_cb=None)

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
                #self._control.start_video()
                
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
