#!/usr/bin/python

import httplib, json
#Younghwan's own module
import weatherUG
#The returned json format is {"epoch" : epoch time, "temp" : temperature, "humidity" : humidity}
GCM_SERVER_API_KEY = 'AIzaSyCig9bJXo86ke32_w5WxziO8s4QRyaoZuI'
GCM_REQUEST_URL = 'gcm-http.googleapis.com'
GCM_REQUEST_SUBPATH = '/gcm/send'
GCM_CLIENT_KEY = [ 'dPHQFUkW3Lc:APA91bFxNqeS2sGZZJbpViLrT8Eh4iUPS6nDbhjNPdHDLlZC0TOlSyAkne38h8UwH1r3xs26iFm_m4G4O6eGzdJOWJW8Vxw3gPfpjeHzdSaH8lytUTuiIvZ78SWYtZN_hgPrNlin8uHO' ]

def noti_server(temp, humi, msg):
        c = httplib.HTTPSConnection(GCM_REQUEST_URL)
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
HIGH_TEMP_THRESHOLD = '70'
LOW_TEMP_THRESHOLD = '60'
def get_data():
        '''Retrieve weather data'''
        conditions = [ Condition(is_above_threshold, notify_server, []) ]
        forecasts = weatherUG.getHourlyForecast("66103", "english")
        for forecast in forecasts:
                args = [forecast['temp'], forecast['humidity']]
                conditions[0].success_args = args[:]
                conditions[0].success_args.append("The threshold was exceeded")
                # TODO: This needs to be better designed for usability. Try to make
                # more user friendly (i.e, key = 'temp' shouldn't be randomly specified
                # and ordering of data shouldn't be so strict
                data = [HIGH_TEMP_THRESHOLD, forecast, 'temp']
                scan_data(data, conditions)
        
def scan_data(data, conditions):
        '''Scan data and determine if specified condition was met. If it was, 
        execute condition success function'''
        for condition in conditions:
                # TODO: Make this more readable while preserving flexibility. Use Data
                # class?
                if condition.is_satisfied(data[0], data[1][data[2]]):
                        condition.success_function(condition.success_args)
                        return # TODO: What if multiple conditions to be tested AND evaluated?
#
# Class used to represent condition for use with data scan.
#
class Condition(object):
       def __init__(self, condition_function, success_function, success_args):
               self.condition_function = condition_function
               self.success_function = success_function
               self.success_args = success_args

       def is_satisfied(self, *args):
               '''Test whether args satisfy the condition function.'''
               return self.condition_function(args)

def is_above_threshold(args):
       threshold = args[0]
       data_to_test = args[1]
       result = False
       if data_to_test > threshold:
               result = True
       return result

def is_below_threshold(args):
       threshold = args[0]
       data_to_test = args[1]
       result = False
       if data_to_test < threshold:
               result = True
       return result
        
def notify_server(args):
        '''Adapter function to adapt noti_server to scan_data
        function'''
        if len(args) != 3:
                raise ValueError("args should be array with three values")
        noti_server(args[0], args[1], args[2])

#Also you can notification to my Android phone by:
# noti_server(temperature, humidity, message)
