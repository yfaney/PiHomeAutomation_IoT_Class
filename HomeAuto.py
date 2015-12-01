#!/usr/bin/python
# Copyright (c) 2015 Younghwan Jang
# Author : Younghwan Jang with modifying Tony DiCola's code, 2014 Adafruit Industries
# See https://github.com/adafruit/Adafruit_Python_DHT/blob/master/examples/AdafruitDHT.py

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys

import Adafruit_DHT
import json

import subprocess, httplib, json, datetime, time

import WeatherUG as WUG

import RESTInterface as RESTI

# Global Variables

GCM_SERVER_API_KEY = 'AIzaSyCig9bJXo86ke32_w5WxziO8s4QRyaoZuI'
GCM_SERVER_API_KEY2 = 'AIzaSyBnKZrBOuJkVN7740MkqN8YCzq8-y8dURg'
GCM_REQUEST_URL = 'gcm-http.googleapis.com'
GCM_REQUEST_SUBPATH = '/gcm/send'
GCM_CLIENT_KEY2 = ['APA91bHNm_f0E4NXvzfppvt6udxHF8KkiA6uCvYFG882yI4KRvFOELfAuyktn2jE44NTrQ0GvR2tg4rXaVgVuyQRzs1lCZUMdffUhD-ccR1JCUoxP9JDqGnM07B6Hj6Opq6ZVtDGxLOrNWncrziuhTsy1JxerkgrUg']

MYSERVER_SENSOR_NAME = 'StudyRoom01'

# How long to wait (in seconds) between measurements.
FREQUENCY_SECONDS      = 120

# Parse command line parameters.
sensor_args = { '11': Adafruit_DHT.DHT11,
				'22': Adafruit_DHT.DHT22,
				'2302': Adafruit_DHT.AM2302 }

dbi = RESTI.dbInterface()
gpioi = RESTI.gpioInterface(RESTI.GPIO_API_URL)

def noti_server(temp, humi, msg, status):
	c = httplib.HTTPSConnection(GCM_REQUEST_URL)
	headers = {}
	headers['Content-Type'] = 'application/json'
	headers['Authorization'] = 'key=' + GCM_SERVER_API_KEY2

	notipayload = {'message' : msg + u"(Temp={0:0.1f}\u2103/Humi={1:0.1f}%)".format(temp, humi), 'temp' : temp, 'humi' : humi, 'status' : status}
	result = dbi.get_gcm_keys()
	gcm_keys = []
	for item in result:
		gcm_keys.append(item['gcm_key'])
	notimsg = {'registration_ids': gcm_keys, 'data' : notipayload}
	c.request("POST", GCM_REQUEST_SUBPATH, json.dumps(notimsg), headers)
	response = c.getresponse()
	print "Notifying to Cellphone..."
	print response.status, response.reason
	data = response.read()
	print data

def push_server(temp, humi):
	try:
		c = httplib.HTTPSConnection(GCM_REQUEST_URL)
		headers = {}
		headers['Content-Type'] = 'application/json'
		headers['Authorization'] = 'key=' + GCM_SERVER_API_KEY
		notipayload = {'tstamp': int(datetime.datetime.now().strftime("%s")), 'temp' : temp, 'humi' : humi }
		notimsg = {'registration_ids':GCM_CLIENT_KEY2, 'data':notipayload }
		c.request("POST", GCM_REQUEST_SUBPATH, json.dumps(notimsg), headers)
		response = c.getresponse()
		print response.status, response.reason
		data = response.read()
		print data
	except Exception,e:
		print "Error while pushing GCM message: %s" % (str(e))

def insert_my_server(p_temp, p_humi, p_msg):
	try:
		print dbi.post_ht_sensor(MYSERVER_SENSOR_NAME, datetime.datetime.now(), p_temp, p_humi, p_msg)
	except Exception,e:
		print "Error while inserting into my server: %s" % (str(e))

def insert_forecast_my_server(zipcode):
	try:
		print dbi.delete_ht_forecast(datetime.datetime.now(), zipcode)
	except Exception,e:
		print str(e)
	try:
		hTForecast = WUG.getHourlyFC_HTSensor(zipcode)
		for hourly in hTForecast:
			print dbi.post_ht_forecast(hourly['tstamp'] * 1000, hourly['zipcode'], hourly['temp'], hourly['humidity'])
	except Exception,e:
		print str(e)
	if (hTForecast is not None):
		return hTForecast

def analyzeFCData(fcData, temp_low, temp_high, humi_low, humi_high):
	now = datetime.datetime.now()
	after3Hours = now + datetime.timedelta(hours=3)
	is_temp = None
	is_humi = None
	message = ""
	for hourly in fcData:
		print ("%f, %f" % (hourly['temp'], hourly['humidity']))
		if(hourly['temp'] < float(temp_low)):
			if(hourly['tstamp'] < int(after3Hours.strftime("%s"))):
				message = 'Outside will get cold soon. Turning heater on...'
				is_temp = "Cold"
				gpioi.heater_onoff(True)
		elif(hourly['temp'] > float(temp_high)):
			if(hourly['tstamp'] < int(after3Hours.strftime("%s"))):
				message = 'Outside will get hot soon. Turning heater off...'
				is_temp = "Hot"
				gpioi.heater_onoff(False)
		if(hourly['humidity'] < float(humi_low)):
			if(hourly['tstamp'] < int(after3Hours.strftime("%s"))):
				message = "%s%s" % (message, 'Outside will get dry soon. Turning humidifier on...')
				is_humi = "Dry"
				gpioi.humier_onoff(True)
		elif(hourly['humidity'] > float(humi_high)):
			if(hourly['tstamp'] < int(after3Hours.strftime("%s"))):
				message = "%s%s" % (message, 'Outside will get humid soon. Turning humidifier off...')
				is_humi = "Humid"
				gpioi.humier_onoff(False)
		notiMsg = ""
		if(is_humi is not None):
			notiMsg = "%s,%s"%(notiMsg, is_humi)
		if(is_temp is not None):
			notiMsg = "%s,%s"%(notiMsg, is_temp)
		if((is_temp is not None) or (is_humi is not None)):
			print message
			noti_server(hourly['temp'], hourly['humidity'], message, notiMsg)
			return

def readPhotoResistor():
	reading = gpioi.get_photo_sensor()
	return reading['output']

# Starts Here!!!

if len(sys.argv) == 7 and sys.argv[1] in sensor_args:
	sensor = sensor_args[sys.argv[1]]
	pin = sys.argv[2]
	temp_low = int(sys.argv[3])
	temp_high = int(sys.argv[4])
	humi_low = int(sys.argv[5])
	humi_high = int(sys.argv[6])
else:
	print 'usage: sudo ./Adafruit_DHT.py [11|22|2302] GPIOpin#'
	print 'example: sudo ./Adafruit_DHT.py 2302 4 - Read from an AM2302 connected to GPIO #4'
	sys.exit(1)
		
# For GCM notification
noticount = 30
# For Forecast
fccount = 30

# Loop forever!
while True:
	#Push the forecast data into the server
	fccount = fccount + 1
	if fccount >= 30:
		fcData = insert_forecast_my_server("66204")
		if(fcData is not None):
			try:
				analyzeFCData(fcData, temp_low, temp_high, humi_low, humi_high)
			except Exception,e:
				print ("Error on FC analysis: %s" % (str(e)))
				pass
		fccount = 0

	humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

	# Note that sometimes you won't get a reading and
	# the results will be null (because Linux can't
	# guarantee the timing of calls to read the sensor).
	# If this happens try again!
	if humidity is not None and temperature is not None:
		print str(datetime.datetime.now()) + 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity)
		message = ""
		is_temp = None
		is_humi = None
		if temperature < temp_low:
			message = '(IoT)The room too cold. Turning heater on...'
			is_temp = "Cold"
			gpioi.heater_onoff(True)
		elif temperature > temp_high:
			message = '(IoT)The room too hot. Turning heater off...'
			is_temp = "Hot"
			gpioi.heater_onoff(False)
		if humidity < humi_low:
			if message != "":
				message = message + "/" + 'The room too dry. Turning humidifier on...'
			else:
				message = '(IoT)The room too dry. Turning humidifier on...'
			is_humi = "Dry"
			gpioi.humier_onoff(True)
		elif humidity > humi_high:
			if message != "":
				message = message + "/" + 'The room too humid. Turning humidifier off...'
			else:
				message = '(IoT)The room too humid. Turning humidifier off...'
			is_humi = "Humid"
			gpioi.humier_onoff(False)
		if message is not None:
			print message

		if is_temp is None and is_humi is None:
			insert_my_server(temperature, humidity, "")
		else:
			noticount = noticount + 1
			if noticount >= 30:
				notiMsg = ""
				if(is_humi is not None):
					notiMsg = "%s,%s"%(notiMsg, is_humi)
				if(is_temp is not None):
					notiMsg = "%s,%s"%(notiMsg, is_temp)
				noti_server(temperature, humidity, message, notiMsg)
				noticount = 0
			if is_temp is not None and is_humi is not None:
				noticount = noticount + 1
				insert_my_server(temperature, humidity,  is_temp + " and " + is_humi)
			elif is_temp is None and is_humi is not None:
				insert_my_server(temperature, humidity, is_humi)
			elif is_temp is not None and is_humi is None:
				noticount = noticount + 1
				insert_my_server(temperature, humidity, is_temp)
		push_server(temperature, humidity)
	else:
		print 'Failed to get reading. Try again!'
	time.sleep(FREQUENCY_SECONDS)
print 'HomeAuto.py Exited...'
