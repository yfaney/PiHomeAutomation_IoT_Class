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
import gspread, json

import subprocess, httplib, json, datetime, time
from oauth2client.client import SignedJwtAssertionCredentials

# Global Variables

# Google Docs account email, password, and spreadsheet name.
GDOCS_EMAIL            = 'YOUR_GMAIL_ID'
GDOCS_PASSWORD         = 'YOUR_GMAIL_PASSWORD'
GDOCS_SPREADSHEET_NAME = 'YOUR_SPREADSHEET_NAME'

GCM_SERVER_API_KEY = 'YOUR_GOOGLE_DEVELOPER_CONSOLE_API_KEY'
GCM_REQUEST_URL = 'android.googleapis.com'
GCM_REQUEST_SUBPATH = '/gcm/send'
GCM_CLIENT_KEY = [ 'YOUR_1ST_CLIENT_KEY_ANDROID_FOR_1HOUR_INTERVAL', 'YOUR_2ND_CLIENT_KEY_ANDROID_FOR_1HOUR_INTERVAL' ]
GCM_CLIENT_KEY2 = ['YOUR_1ST_CLIENT_KEY_ANDROID_FOR_2MINUTE_INTERVAL', 'YOUR_2ND_CLIENT_KEY_ANDROID_FOR_2MINUTE_INTERVAL']

# For OAuth2 part!
json_key = json.load(open('gspread_client_key.json'))
scope = ['https://spreadsheets.google.com/feeds']
credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)

# How long to wait (in seconds) between measurements.
FREQUENCY_SECONDS      = 120

# Parse command line parameters.
sensor_args = { '11': Adafruit_DHT.DHT11,
                                '22': Adafruit_DHT.DHT22,
                                '2302': Adafruit_DHT.AM2302 }

# Functions!
gc = None
worksheet = None



def noti_server(temp, humi, msg):
        c = httplib.HTTPSConnection(GCM_REQUEST_URL)
        headers = {}
        headers['Content-Type'] = 'application/json'
        headers['Authorization'] = 'key=' + GCM_SERVER_API_KEY

        notipayload = {'message' : msg + u"(Temp={0:0.1f}\u2103/Humi={1:0.1f}%)".format(temp, humi), 'temp' : temp, 'humi' : humi}
        notimsg = {'registration_ids': GCM_CLIENT_KEY, 'data' : notipayload}
        c.request("POST", GCM_REQUEST_SUBPATH, json.dumps(notimsg), headers)
        response = c.getresponse()
        print response.status, response.reason
        data = response.read()
        print data

def push_server(temp, humi):
        c = httplib.HTTPSConnection(GCM_REQUEST_URL)
        headers = {}
        headers['Content-Type'] = 'application/json'
        headers['Authorization'] = 'key=' + GCM_SERVER_API_KEY
        notipayload = {'temp' : temp, 'humi' : humi }
        notimsg = {'registration_ids':GCM_CLIENT_KEY2, 'data':notipayload }
        c.request("POST", GCM_REQUEST_SUBPATH, json.dumps(notimsg), headers)
        response = c.getresponse()
        print response.status, response.reason
        data = response.read()
        print data

def auth_open_sheet(spreadsheet):
        """Connect to Google Docs with OAuth2 and return the first worksheet"""
        try:
                gc = gspread.authorize(credentials)
                sheet = gc.open(spreadsheet).sheet1
                return sheet
        except Exception, e:
                if gc is None:
                        print 'Unable to login. Check OAuth key.'
                else:
                        print 'Unable to get spreadsheet. Check the spreadsheet name.'
                print str(e)
                sys.exit(1)

def login_open_sheet(email, password, spreadsheet):
        """Connect to Google Docs spreadsheet and return the first worksheet."""
        try:
                gc = gspread.login(email, password)
                #print 'successfully logged in'
                sheet = gc.open(spreadsheet).sheet1
                return sheet
        except:
                if gc is None:
                        print 'Unable to login.  Check email and password.'
                else:
                        print 'Unable to get spreadsheet. Check the spreadsheet name.'
                sys.exit(1)

def send_to_google_drive(sheet, p_temp, p_humi, p_msg):
        # Append the data in the spreadsheet, including a timestamp
        try:
                if p_temp is not None and p_humi is not None:
                        row = [ datetime.datetime.now(), p_temp, p_humi, p_msg ]
                        sheet.append_row(row)
                        #print (row)
                        print 'Wrote a row to {0}'.format(GDOCS_SPREADSHEET_NAME)
                else:
                        print 'Something wrong. Not written.'
                return sheet
        except Exception, e:
                # Error appending data, most likely because credentials are stale.
                # Null out the worksheet so a login is performed at the top of the loop.
                print 'Append error, logging in again'
                print str(e)
                """Append Error so retry one time"""
                sheet = auth_open_sheet(GDOCS_SPREADSHEET_NAME)
                row = [ datetime.datetime.now(), p_temp, p_humi, p_msg ]
                try:
                        sheet.append_row(row)
                        return sheet
                except Exception, e:
                        """If it does not work again, make worksheet null"""
                        print str(e)
                        return None

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
        print 'example: sudo ./Adafruit_DHT.py 2302 4 23 25 45 60 - Read from an AM2302 connected to GPIO #4 and notify if the temperature or humidity is out of 23~25*C or 45~60%'
        sys.exit(1)

# For GCM notification
noticount = 30

# Loop forever!
while True:
        # Login if necessary.
        if worksheet is None:
                worksheet = auth_open_sheet(GDOCS_SPREADSHEET_NAME)

        # Try to grab a sensor reading.  Use the read_retry method which will retry up
        # to 15 times to get a sensor reading (waiting 2 seconds between each retry).
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
                        message = 'The room too cold. Turn heater on!'
                        is_temp = "Cold"
                elif temperature > temp_high:
                        message = 'The room too hot. Turn cooler on!'
                        is_temp = "Hot"
                if humidity < humi_low:
                        if message != "":
                                message = message + "/" + 'The room too dry. Turn the humidifier on!'
                        else:
                                message = 'The room too dry. Turn the humidifier on!'
                        is_humi = "Dry"
                elif humidity > humi_high:
                        if message != "":
                                message = message + "/" + 'The room too humid. Turn the humidifier off!'
                        else:
                                message = 'The room too humid. Turn the humidifier off!'
                        is_humi = "Humid"
                if message is not None:
                        print message

                if is_temp is not None and is_humi is not None:
                        noticount = noticount + 1
                        worksheet = send_to_google_drive(worksheet, temperature, humidity, is_temp + " and " + is_humi)
                        if noticount >= 30:
                                noti_server(temperature, humidity, message)
                                noticount = 0
                elif is_temp is None and is_humi is not None:
                        noticount = noticount + 1
                        worksheet = send_to_google_drive(worksheet, temperature, humidity, is_humi)
                        if noticount >= 30:
                                noti_server(temperature, humidity, message)
                                noticount = 0
                elif is_temp is not None and is_humi is None:
                        noticount = noticount + 1
                        worksheet = send_to_google_drive(worksheet, temperature, humidity, is_temp)
                        if noticount >= 30:
                                noti_server(temperature, humidity, message)
                                noticount = 0
                else:
                        worksheet = send_to_google_drive(worksheet, temperature, humidity, "")
                push_server(temperature, humidity)
        else:
                print 'Failed to get reading. Try again!'
        time.sleep(FREQUENCY_SECONDS)
pi@mypifaney01 ~ $
