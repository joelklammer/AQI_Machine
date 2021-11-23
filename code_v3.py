#!/usr/bin/env python2
import pymysql.cursors
import serial
import time
import datetime

def toAQI(pm):
    pm = int(float(pm)*1000)
    if (pm <= 12): #AQI 0 - 50
        return int( (pm - 0.0)/(12.0 - 0.0)*(50.0 - 0.0) + 0.0 )
    elif (pm <= 35.4): #AQI 51 - 100
        return int( (pm - 12.1)/(35.4 - 12.1)*(100.0 - 51.0) + 51 )
    elif (pm <= 55.4): #AQI 101 - 150
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

def process(s):
    s = s.strip() 
    ls = s.strip().split()

    if ls[1] == '------------':
        error = 'No Error'
    elif ls[1] == '-----------T':
        error = 'Tape Error'
    else:
        error = 'Unknown Error: ' + str(ls[1])

    print(ls)
    assert len(ls) == 10

    tags = ('time', 'flags', 'conc', 'qtot', '01_no_V', '02_WS_MPS', '03_no_V', '04_RH_%', '05_no_V', '06_AT_C')
    d = dict(zip(tags, ls))

    #tmp = d['date'].split('/') # month/day/year?

    ts = time.time()
    if (abs(time.timezone) != 28800):
        # incorrect time zone
        ts += 28800 # add +8

    t = datetime.datetime.fromtimestamp(ts)
    mon = str(t.month)
    if len(mon) == 1:
        mon = '0' + mon
    day = str(t.day)
    if len(day) == 1:
        day = '0' + day

    d['date'] = '-'.join([str(t.year), mon, day])

    datetime2 = d['date'] + ' ' + d['time'] + ':00'

    print(datetime2)
    #print()

    d['AQI'] = str(toAQI(d['conc']))

    print(d)

    # Connect to the database
    connection = pymysql.connect(host='10.0.20.25', #172.18.10.28
                                 user='aqiMachine', # Pascal
                                 password='LEDcube2718',
                                 db='outdoorPM25', #PM25
                                 charset='utf8mb4', #_general_ci
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            # Create a new record
            sql = "INSERT INTO `Data` (`Date`, `AQI`, `Conc`,`Qtot`,`Temp`,`Errors`) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}')"
            sql = sql.format(
                datetime2,
                d['AQI'],
                d['conc'],
                d['qtot'],
                d['06_AT_C'],
                error
                )
            cursor.execute(sql)

            print(sql)

        # connection is not autocommit by default. So you must commit to save
        # your changes.

        # format: YYYY-MM-DD HH:mm:SS

        connection.commit()
    finally:
        connection.close()


def main():
    ser = serial.Serial(
        port='/dev/ttyUSB0',\
        baudrate=9600,\
        parity=serial.PARITY_NONE,\
        stopbits=serial.STOPBITS_ONE,\
        bytesize=serial.EIGHTBITS,\
        timeout=0)

    for i in range(3):
        ser.write(b'\r\n')
        time.sleep(0.1)
    time.sleep(1)
    ser.write(b'1')

    data = bytearray()

    finished = False
    #counter = 0
    try:
        while not finished:
            for c in ser.read():
                #counter += 1
                data.append(c)

            if b'Valid Daily Conc' in data:
                print('Done reading data')
                break
            #if counter > 2000:
            #    print('Too many loops')
            #    break

    finally:
        ser.close()

    # process the data!
    data = [i.strip() for i in data.decode().split('\n')]

    index = None
    for i in range(len(data)):
        if data[i].startswith('=========='):
            index = i
            break

    if index == None:
        raise ValueError('Error: Did not find line with "=========="')

    data = list(reversed(data[index+1:]))

    for line in data:
        if '--------' in line: # first data line aka last data line cause reversal
            print('->',line)
            process(line)
            break

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('--- Error ---')
        print(e)
