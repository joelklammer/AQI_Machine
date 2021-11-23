#!/usr/bin/python
import serial
import time


# variables
finished = False
line = []

# functions
def toAQI(pm):
  pm = int(pm)
  if (pm <= 12):      #AQI 0 - 50
    return int( (pm - 0.0)/(12.0 - 0.0)*(50.0 - 0.0) + 0.0 )
  elif (pm <= 35.4):  #AQI 51 - 100
    return int( (pm - 12.1)/(35.4 - 12.1)*(100.0 - 51.0) + 51 )
  elif (pm <= 55.4):  #AQI 101 - 150
    return int( (pm - 35.5)/(55.4 - 35.5)*(150.0- 101.0) + 101 )
  elif (pm <= 150.4): #AQI 151 - 200
    return int( (pm - 55.5)/(150.4 - 55.5)*(200.0 - 151.0) + 151 )
  elif (pm <= 250.4): #AQI 201 - 300
    return int( (pm - 150.5)/(250.4 - 150.5)*(300.0 - 201.0) + 201 )
  elif (pm <= 350.4): #AQI 301 - 400
    return int( (pm - 250.5)/(350.4 - 250.5)*(400.0 - 301.0) + 301 )
  elif (pm <= 500.0): #AQI 401 - 500
    return int( (pm - 350.5)/(500.0 - 350.5)*(500.0 - 401.0) + 401 )
  else:
    return pm  

ser = serial.Serial(
    port='/dev/ttyUSB0',\
    baudrate=9600,\
    parity=serial.PARITY_NONE,\
    stopbits=serial.STOPBITS_ONE,\
    bytesize=serial.EIGHTBITS,\
        timeout=0)

try:
  # This will append the existing file
  f = open("/media/networkshare/science/pm25/PM25history.txt", "a")
  try:

    for i in range(5):
       ser.write("\r\n")
       time.sleep(0.2)
    time.sleep(1)
    ser.write("1")
    
    while not finished:
      for c in ser.read():
        line.append(c)
        joined_line = ''.join(str(v) for v in line) #Make a string from array

        if c == '\n':
          if joined_line.find("Report for") != -1:    #Located Date
              i = joined_line.find("Report for")
              date = joined_line[13:23]

          if joined_line.find("------------") != -1:  #Normal Data Line
              f.write(date)
              f.write(' ')
              f.write(joined_line)

          if joined_line.find("Valid Daily Conc") != -1: #End
              finished = True
              break
          line = []

    ser.close()

  finally:
    f.close()
except IOError:
  pass
