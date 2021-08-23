import time, RPi.GPIO as GPIO
import urllib
import sys, string, os
import Adafruit_DHT
from datetime import datetime
import time
import _mysql
import smbus
from ctypes import c_short

DEVICE = 0x77      # 預設 I2C 位址
bus = smbus.SMBus(1)  # Rev 2 Pi uses 1 

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

GPIO.setmode(GPIO.BOARD)

#while True:
humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

if humidity is not None and temperature is not None:
    print("Temp={0:0.2f}*C Humidity={1:0.2f}%".format(temperature, humidity))
else:
    print("Failed to retrieve data from DHT22 sensor")

result = datetime.now().strftime("%Y-%m-%d %I:%M:%S %P")
print(result)
time.sleep(1)

def convertToString(data):
  # Simple function to convert binary data into a string
  return str((data[1] + (256 * data[0])) / 1.2)

def getShort(data, index):
  # return two bytes from data as a signed 16-bit value
  return c_short((data[index] << 8) + data[index + 1]).value

def getUshort(data, index):
  # return two bytes from data as an unsigned 16-bit value
  return (data[index] << 8) + data[index + 1]

def readBmp180Id(addr=DEVICE):
  # Register Address
  REG_ID     = 0xD0

  (chip_id, chip_version) = bus.read_i2c_block_data(addr, REG_ID, 2)
  return (chip_id, chip_version)
  
def readBmp180(addr=DEVICE):
  # Register Addresses
  REG_CALIB  = 0xAA
  REG_MEAS   = 0xF4
  REG_MSB    = 0xF6
  REG_LSB    = 0xF7
  # Control Register Address
  CRV_TEMP   = 0x2E
  CRV_PRES   = 0x34 
  # Oversample setting
  OVERSAMPLE = 3    # 0 - 3
  
  # Read calibration data
  # Read calibration data from EEPROM
  cal = bus.read_i2c_block_data(addr, REG_CALIB, 22)

  # Convert byte data to word values
  AC1 = getShort(cal, 0)
  AC2 = getShort(cal, 2)
  AC3 = getShort(cal, 4)
  AC4 = getUshort(cal, 6)
  AC5 = getUshort(cal, 8)
  AC6 = getUshort(cal, 10)
  B1  = getShort(cal, 12)
  B2  = getShort(cal, 14)
  MB  = getShort(cal, 16)
  MC  = getShort(cal, 18)
  MD  = getShort(cal, 20)

# 讀取壓力
  bus.write_byte_data(addr, REG_MEAS, CRV_PRES + (OVERSAMPLE << 6))
  time.sleep(0.04)
  (msb, lsb, xsb) = bus.read_i2c_block_data(addr, REG_MSB, 3)
  UP = ((msb << 16) + (lsb << 8) + xsb) >> (8 - OVERSAMPLE)

# Refine pressure
  B6  = B5 - 4000
  B62 = B6 * B6 >> 12
  X1  = (B2 * B62) >> 11
  X2  = AC2 * B6 >> 11
  X3  = X1 + X2
  B3  = (((AC1 * 4 + X3) << OVERSAMPLE) + 2) >> 2

  X1 = AC3 * B6 >> 13
  X2 = (B1 * B62) >> 16
  X3 = ((X1 + X2) + 2) >> 2
  B4 = (AC4 * (X3 + 32768)) >> 15
  B7 = (UP - B3) * (50000 >> OVERSAMPLE)

  P = (B7 * 2) / B4

  X1 = (P >> 8) * (P >> 8)
  X1 = (X1 * 3038) >> 16
  X2 = (-7357 * P) >> 16
  pressure = P + ((X1 + X2 + 3791) >> 4)

  # 計算高度
  altitude = 44330.0 * (1.0 - pow(pressure / 101325.0, (1.0/5.255)))
  return (temperature/10.0,pressure/ 100.0,round(altitude,2))

def main():

  (chip_id, chip_version) = readBmp180Id()
  print "Chip ID     :", chip_id
  print "Version     :", chip_version,"\n"
  # 連續偵測 5次
  for i in range(0,5):
     (pressure,altitude)=readBmp180()
     print "壓力 :", pressure, "mbar"
     print "高度 :", altitude, "m\n"
     time.sleep(2)

if __name__=="__main__":   
  main()
  time.sleep(2)
'''
try:
    	con = _mysql.connect('140.112.94.126', 'root', '303', 'bee')
    	#con.query("SELECT VERSION()")
    	#result = con.use_result()
    	#print "MySQL version: %s" %  result.fetch_row()[0]
	    sqlstr="INSERT INTO ccd (nodeid,temp_in,humi_in,temp_out,\
        humi_out,pest_in,pest_out,illumination,Atmospheric_pressure,time) VALUES('" + sys.argv[1] +"','" + sys.argv[2] +"',\
        '" + sys.argv[3] +"','" + sys.argv[4] +"','" + sys.argv[5] +"','" + sys.argv[6] +"','" + sys.argv[7] +"','" + sys.argv[8] +"','" + sys.argv[9] +"',now())" 
	   
	    con.query(sqlstr)
    
except _mysql.Error, e:
  
    	print "Error %d: %s" % (e.args[0], e.args[1])
    	sys.exit(1)

finally:
    
    	if con:
        		con.close()
        		
'''

def fetch_thing(url, params, method):
    params = urllib.urlencode(params)
    if method=='POST':
        f = urllib.urlopen(url, params)
    else:
        f = urllib.urlopen(url+'?'+params)
    return (f.read(), f.code)

content, response_code = fetch_thing(
                                     'http://140.112.94.126',
                                     {'id': 1, 'Temp': Temp, 'Humidity':Humidity, 'result':result, 'pressure':pressure,'altitude':altitude},
                                     'GET'
                                     )