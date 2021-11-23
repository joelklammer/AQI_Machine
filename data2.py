#!/usr/bin/python
import serial
import time

# ***  NOTE: Code assumes that PM sampler's internal clock ***
# ***  is set +15 minutes ahead of local time so that it   ***
# ***  reports data at HH:45.  (i.e. 8:15 machine = 8:00)  ***

# variables
line = []
finished = False

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
        timeout=60)

try:
  # This will create a new file or **overwrite an existing file**.
  f = open("/var/www/data.html", "w")
  try:
    f.write('<!DOCTYPE HTML>\n')
    f.write('<html>\n')
    f.write('<head>\n')
    f.write('  <title>Concordia AQI</title>\n')
    f.write('  <meta http-equiv="refresh" content="3600">\n')
    f.write('  <style type="text/css">\n')
    f.write('     H1 {font-family: \'Lucida Sans Unicode\', \'Lucida Grande\', sans-serif;\n')
    f.write('         font-weight: bold; text-align: center; font-size: 64px; color: #000;}\n')
    f.write('     H2 {font-family: \'Lucida Sans Unicode\', \'Lucida Grande\', sans-serif;\n')
    f.write('         font-style: italic; text-align: center; font-size: 10px; color: #666;}\n')
    f.write('  </style>\n')
    f.write('  <script type="text/javascript">\n')
    f.write('  window.onload = function () {\n')
    f.write('    var chart = new CanvasJS.Chart("chartContainer",\n')
    f.write('    {\n')
    f.write('      title:{ text: "Concordia Hourly AQI Readings" },\n')
    f.write('      axisX: {\n')
    f.write('        title: "Local Time",\n')
    f.write('        gridThickness: 1,\n')
    f.write('        minimum: new Date( Date.UTC(2012, 01, 1, -8, 45) ),\n')
    f.write('        valueFormatString: "HH:mm",\n')
    f.write('        interval: 30,\n')
    f.write('        intervalType: "minute",\n')
    f.write('        labelAngle: -50\n')
    f.write('      },\n')
    f.write('      axisY:{ \n')
    f.write('        title: "AQI",\n')
    f.write('        interval:50,\n')
    f.write('        labelAngle: 0,\n')
    f.write('        maximum: 400,\n')
    f.write('        includeZero: true\n')
    f.write('      },\n')
    f.write('      data: [\n')
    f.write('      {\n')
    f.write('        indexLabelFontColor: "blue",\n')
    f.write('        type: "area",\n')
    f.write('        color: "rgba(0,75,141,0.5)",\n')
    f.write('        dataPoints: [\n')

    for i in range(6):
       ser.write("\r\n")
       time.sleep(0.2)
    time.sleep(2)
    ser.write("1")
    
    while not finished:
      for c in ser.read():
        line.append(c)
        joined_line = ''.join(str(v) for v in line) #Make a string from array

        if c == '\n':
          if joined_line.find("------------") != -1:  #Normal Data Line
              i = joined_line.find("------------") 
              time = joined_line[0:i-4]
              AQI = joined_line[i+16:i+19]
              f.write('        { x: new Date( Date.UTC(2012, 01, 1, ')
              f.write(str( int(time)-9 ))
              f.write(', 45) ), y: ')
              f.write(str(toAQI(AQI)))
              f.write(', indexLabel: "')
              f.write(str(toAQI(AQI)))
              f.write('"},\n')
          if joined_line.find("-----------T") != -1:  #Tape Error Flag
              i = joined_line.find("-----------T")
              time = joined_line[0:i-4]
              f.write('        { x: new Date( Date.UTC(2012, 01, 1, ')
              f.write(str( int(time)-9 ))
              f.write(', 45) ), y: 000, indexLabel: "Tape Err"},\n')
          if joined_line.find("--M---------") != -1:  #Maintenance Alarm Flag
              i = joined_line.find("--M---------")
              time = joined_line[0:i-4]
              f.write('        { x: new Date( Date.UTC(2012, 01, 1, ')
              f.write(str( int(time)-9 ))
              f.write(', 45) ), y: 000, indexLabel: "Maintenance"},\n')
          if joined_line.find("-------F----") != -1:  #Flow Rate Flag
              i = joined_line.find("-------F----")
              time = joined_line[0:i-4]
              f.write('        { x: new Date( Date.UTC(2012, 01, 1, ')
              f.write(str( int(time)-9 ))
              f.write(', 45) ), y: 000, indexLabel: "Flow Err"},\n')
          if joined_line.find("Valid Daily Conc") != -1: #End
              finished = True
              break
          line = []

    ser.close()

    f.write('        ]\n')
    f.write('      }\n')
    f.write('      ]\n')
    f.write('    });\n\n')
    f.write('    chart.render();\n')
    f.write('  }\n')
    f.write('  </script>\n')
    f.write(' <script type="text/javascript" src="./canvasjs/canvasjs.min.js"></script></head>\n')
    f.write('<body>\n')
    f.write('  <div id="chartContainer" style="height: 400px; width: 100%;">\n')
    f.write('  </div>\n')
    f.write('  <H1>Current AQI: ')
    f.write(str(toAQI(AQI)))
    f.write('</H1>\n')
    f.write('  <H2>PM2.5 concentration: ')
    f.write(str(int(AQI))+' ')
    f.write('&mu;') #u'\u03BC'
    f.write('g/m<sup>3</sup><br>\n')
    f.write('  Last reading: ')
    f.write(str(int(time)-1))
    f.write(':45</H2>\n')
    f.write('</body>\n')
    f.write('</html>\n')
  finally:
    f.close()
except IOError:
  pass

# Write simple text file for Filter Controller to read
try:
  f = open("/var/www/data.txt", "w")
  try:
    f.write(str(toAQI(AQI)))
  finally:
    f.close()
except IOError:
  print("failed to write controller file!")
  pass

# Write text file to Science share
try:
  f = open("/media/networkshare/science/pm25/PM25.txt", "w")
  try:
    f.write(str(toAQI(AQI)))
  finally:
    f.close()
except IOError:
  pass
