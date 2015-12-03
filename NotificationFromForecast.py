#!/usr/bin/python

import httplib, json
#Younghwan's own module
import weatherUG
#The returned json format is {"epoch" : epoch time, "temp" : temperature, "humidity" : humidity}
GCM_SERVER_API_KEY = 'AIzaSyBnKZrBOuJkVN7740MkqN8YCzq8-y8dURg'
GCM_REQUEST_URL = 'gcm-http.googleapis.com'
GCM_REQUEST_SUBPATH = '/gcm/send'
GCM_CLIENT_KEY = [ 'dPHQFUkW3Lc:APA91bFxNqeS2sGZZJbpViLrT8Eh4iUPS6nDbhjNPdHDLlZC0TOlSyAkne38h8UwH1r3xs26iFm_m4G4O6eGzdJOWJW8Vxw3gPfpjeHzdSaH8lytUTuiIvZ78SWYtZN_hgPrNlin8uHO' ]

def noti_server(temp, humi, msg):
        c = httplib.HTTPSConnection(GCM_REQUEST_URL)
        headers = {}
        headers['Content-Type'] = 'application/json'
        headers['Authorization'] = 'key=' + GCM_SERVER_API_KEY2

        notipayload = {'message' : msg + u"(Temp={0:0.1f}\u2103/Humi={1:0.1f}%)".format(temp, humi), 'temp' : temp, 'humi' : humi}
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

#Also you can notification to my Android phone by:
# noti_server(temperature, humidity, message)
