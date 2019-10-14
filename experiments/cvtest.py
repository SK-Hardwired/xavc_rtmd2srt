
import cv2
import numpy as np
import sys

import numpy_indexed as npi

# Create a VideoCapture object and read from input file
# If the input is the camera, pass 0 instead of the video file name
cap = cv2.VideoCapture(sys.argv[1])

out = cv2.VideoWriter('outpy.avi',cv2.VideoWriter_fourcc('X','V','I','D'), 29.97, (3840,2160))

# Check if camera opened successfully
if (cap.isOpened()== False):
  print("Error opening video stream or file")

gdata = np.loadtxt(sys.argv[2], delimiter=',', skiprows=1);

#sys.exit(0)

gdata[:,1]/=gdata[:,3]
gdata[:,2]/=gdata[:,3]

#print (gdata[:,5])

# Read until video is completed
i = -1
while(cap.isOpened()):
  # Capture frame-by-frame
  ret, frame = cap.read()
  if ret == True:
    # Display the resulting frame
    i+=1
    #print(frame.shape)
    rows,cols,rgb = frame.shape
    M = np.float32([[1,0,(gdata[i,1])],[0,1,(gdata[i,2])]])
    frame = cv2.warpAffine(frame,M,(-cols,-rows))
    cv2.namedWindow ('Frame',cv2.WINDOW_NORMAL)
    cv2.imshow('Frame',frame)
    out.write(frame)
    # Press Q on keyboard to  exit
    if cv2.waitKey(25) & 0xFF == ord('q'):
      break

  # Break the loop
  else:
    break

# When everything done, release the video capture object
cap.release()

# Closes all the frames
cv2.destroyAllWindows()



"""
import cv2

cap = cv2.VideoCapture('C:\\MyWork\\temp\\acam\\C0121.MP4')
ret, current_frame = cap.read()
previous_frame = current_frame

while(cap.isOpened()):
    current_frame_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
    previous_frame_gray = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)

    frame_diff = cv2.absdiff(current_frame_gray,previous_frame_gray)

    cv2.imshow('frame diff ',frame_diff)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    previous_frame = current_frame.copy()
    ret, current_frame = cap.read()

cap.release()
cv2.destroyAllWindows()
"""
