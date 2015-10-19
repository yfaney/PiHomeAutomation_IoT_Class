#!/usr/bin/python

import httplib, json
import copy
#Younghwan's own module
import weatherUG
#The returned json format is {"epoch" : epoch time, "temp" : temperature, "humidity" : humidity}
GCM_SERVER_API_KEY = 'AIzaSyCig9bJXo86ke32_w5WxziO8s4QRyaoZuI'
GCM_REQUEST_URL = 'gcm-http.googleapis.com'
GCM_REQUEST_SUBPATH = '/gcm/send'
GCM_CLIENT_KEY = [ 'dPHQFUkW3Lc:APA91bFxNqeS2sGZZJbpViLrT8Eh4iUPS6nDbhjNPdHDLlZC0TOlSyAkne38h8UwH1r3xs26iFm_m4G4O6eGzdJOWJW8Vxw3gPfpjeHzdSaH8lytUTuiIvZ78SWYtZN_hgPrNlin8uHO' ]

def noti_server(data, msg):
        c = httplib.HTTPSConnection(GCM_REQUEST_URL)
        temp = data.temp
        humi = data.humidity
        print temp, humi, msg # For debug
        headers = {}
        headers['Content-Type'] = 'application/json'
        headers['Authorization'] = 'key=' + GCM_SERVER_API_KEY

        notipayload = {'message' : msg + "(Temp={0:0.1f}\u2103/Humi={1:0.1f}%)".format(float(temp), float(humi)), 'temp' : temp, 'humi' : humi}
        notimsg = {'registration_ids': GCM_CLIENT_KEY, 'data' : notipayload}
        c.request("POST", GCM_REQUEST_SUBPATH, json.dumps(notimsg), headers)
        response = c.getresponse()
        print "Notifying to Cellphone..."
        print response.status, response.reason
        data = response.read()
        print data

#Please work here.
#You can get the forecast data by:
# forecast = weatherUG.getHourlyForecast(zipcode, "english")
HIGH_TEMP_THRESHOLD = '90'
LOW_TEMP_THRESHOLD = '70'
ZIPCODE = '66103'
def get_data():
        '''Retrieve weather data'''
        high_temp_condition = ThresholdCondition(HIGH_TEMP_THRESHOLD)
        high_temp_condition.condition_function = high_temp_condition.is_less_than
        high_temp_condition.success_function = notify_server
        low_temp_condition = ThresholdCondition(LOW_TEMP_THRESHOLD)
        low_temp_condition.condition_function = low_temp_condition.is_greater_than
        low_temp_condition.success_function = notify_server
        conditions = [ high_temp_condition, low_temp_condition ]

        forecasts = weatherUG.getHourlyForecast(ZIPCODE, "english")

        for forecast in forecasts:
                high_temp_condition.success_args = [copy.deepcopy(forecast),
                                                    "High temp threshold breach"]
                low_temp_condition.success_args = [copy.deepcopy(forecast), 
                                                    "Low temp threshold breach"]
                data = forecast.temp
                scan(data, conditions)
        
def scan(data, conditions):
        '''Scan data and determine if specified conditions are met. If met, 
        execute condition success function'''
        for condition in conditions:
                if condition.is_satisfied(data):
                        condition.success_function(condition.success_args)
                        return # TODO: What if multiple conditions to be tested AND evaluated?
#
# "Abstract" class used to represent condition for use with data scan.
#
class Condition(object):
       def __init__(self, condition_name):
               self.condition_name = condition_name
               self.condition_function = None
               self.success_function = None
               self.success_args = None

       def is_satisfied(self, *args):
               '''Test whether args satisfy the condition function.'''
               return self.condition_function(args)

class ThresholdCondition(Condition):
       def __init__(self, threshold):
               Condition.__init__(self, "threshold condition")
               self.threshold = threshold

       def is_less_than(self, value):
               result = False
               if value > self.threshold:
                       result = True
               return result

       def is_greater_than(self, value):
               result = False
               if value < self.threshold:
                       result = True
               return result

       def is_satisfied(self, value):
               return self.condition_function(value)
       

def notify_server(args):
        '''Adapter function to adapt noti_server to scan_data
        function'''
        if len(args) != 2:
                raise ValueError("args should be array with three values")
        noti_server(args[0], args[1])

#Also you can notification to my Android phone by:
# noti_server(temperature, humidity, message)
