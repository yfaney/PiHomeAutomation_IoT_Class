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
import gspread

import subprocess, httplib, urllib2, json, datetime, time, requests

# Global Variables

# Google Docs account email, password, and spreadsheet name.
GDOCS_EMAIL            = 'Your Google e-Mail Address'
GDOCS_PASSWORD         = 'Your Google Password'
GDOCS_SPREADSHEET_NAME = 'Your Spreadsheet File Name'

# How long to wait (in seconds) between measurements.
FREQUENCY_SECONDS      = 60

# Parse command line parameters.
sensor_args = { '11': Adafruit_DHT.DHT11,
                                '22': Adafruit_DHT.DHT22,
                                '2302': Adafruit_DHT.AM2302 }

# Functions!
worksheet = None

def noti_server(temp, humi, msg):
        headers = {'Content-type':'application/json', 'Accept':'topocosts/json'}
        r = requests.post(URL_PUSH_NOTI, data=costJson, headers=headers)
        print r.text

def login_open_sheet(email, password, spreadsheet):
        """Connect to Google Docs spreadsheet and return the first worksheet."""
        try:
                gc = gspread.login(email, password)
                print 'successfully logged in'
                worksheet = gc.open(spreadsheet).sheet1
                return worksheet
        except:
                print 'Unable to login and get spreadsheet.  Check email, password, spreadsheet name.'
                sys.exit(1)

def send_to_google_drive(p_worksheet, p_temp, p_humi, p_msg):
        # Append the data in the spreadsheet, including a timestamp
        try:
                row = [ datetime.datetime.now(), p_temp, p_humi, p_msg ]
                p_worksheet.append_row(row)
                #print (row)
                print 'Wrote a row to {0}'.format(GDOCS_SPREADSHEET_NAME)
        except:
                # Error appending data, most likely because credentials are stale.
                # Null out the worksheet so a login is performed at the top of the loop.
                print 'Append error, logging in again'
                worksheet = None


# Starts Here!!!

if len(sys.argv) == 7 and sys.argv[1] in sensor_args:
        sensor = sensor_args[sys.argv[1]]
        pin = sys.argv[2]
        temp_low = sys.argv[3]
        temp_high = sys.argv[4]
        humi_low = sys.argv[5]
        humi_high = sys.argv[6]
else:
        print 'usage: sudo ./Adafruit_DHT.py [11|22|2302] GPIOpin#'
        print 'example: sudo ./Adafruit_DHT.py 2302 4 - Read from an AM2302 connected to GPIO #4'
        sys.exit(1)

# Loop forever!
while True:
        # Login if necessary.
        if worksheet is None:
                worksheet = login_open_sheet(GDOCS_EMAIL, GDOCS_PASSWORD, GDOCS_SPREADSHEET_NAME)

        # Try to grab a sensor reading.  Use the read_retry method which will retry up
        # to 15 times to get a sensor reading (waiting 2 seconds between each retry).
        humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

        # Note that sometimes you won't get a reading and
        # the results will be null (because Linux can't
        # guarantee the timing of calls to read the sensor).
        # If this happens try again!
        if humidity is not None and temperature is not None:
                print 'Temp={0:0.2f}*C  Humidity={1:0.2f}%'.format(temperature, humidity)
                is_temp = None
                is_humi = None
                if temperature < temp_low:
                        print 'The room too cold. Shut the window and heat the room!'
                        is_temp = "Hot"
                elif temperature > temp_high:
                        print 'The room too hot. Open the window and cool the room!'
                        is_temp = "Cold"

                if humidity < humi_low:
                        print 'The room is too dry. Turn the humidifier on!'
                        is_humi = "Dry"
                elif humidity > humi_low:
                        print 'The roo is too humid. Turn the humidifier off!'
                        is_humi = "Humid"

                if is_temp is not None and is_humi is not None:
                        send_to_google_drive(worksheet, temperature, humidity, is_temp + " and " + is_humi)
                elif is_temp is None and is_humi is not None:
                        send_to_google_drive(worksheet, temperature, humidity, is_humi)
                elif is_temp is not None and is_humi is None:
                        send_to_google_drive(worksheet, temperature, humidity, is_humi)
                else:
                        send_to_google_drive(worksheet, temperature, humidity, "")
        else:
                print 'Failed to get reading. Try again!'
        time.sleep(FREQUENCY_SECONDS)
pi@mypifaney01 ~/Adafruit_Python_DHT/examples $
