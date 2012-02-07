"""recognition test code to see if I can pass data from navdat to my function to move in reosponse to a target detected!"""
import json, socket, time, navdata


def main():
       # a=json.dumps({ 'type': 'visiondetect', 'features': features })
       vdb = navdata.VisionDetectBlock()
       if (vdb.json()== {"type": "visiondetect", "features":[]}):
           print " 000000000000000000000000000000000000000000000000000"
       else:
           print "got it"
           print vdb.



if __name__ == '__main__':
  main()
