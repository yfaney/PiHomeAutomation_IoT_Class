#!/usr/bin/python
# Copyright (c) 2015 Younghwan Jang
# Author : Younghwan Jang

from flask import Flask, render_template, request
from flask.ext.cors import CORS
import datetime, time
import RPi.GPIO as GPIO
import json
app = Flask(__name__)
CORS(app)
#cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
#Set GPIO port numbering as BCM(Not circuit pin no)
GPIO.setmode(GPIO.BCM)

#Light for GPIO17
GPIO.setup(17, GPIO.OUT)

#GPIO.setup(11, GPIO.OUT)
#GPIO.setup(12, GPIO.OUT)
#GPIO.setup(13, GPIO.OUT)

#DC Motor + - for GPIO20, GPIO21. Do Not USE 20 & 21 because other program uses!
#GPIO.setup(20, GPIO.OUT)
#GPIO.setup(21, GPIO.OUT)


#Photo for GPIO22
#GPIO.setup(22, GPIO.OUT)

#Heater for GPIO23
GPIO.setup(23, GPIO.OUT)
#Humidifier for GPIO24
GPIO.setup(24, GPIO.OUT)

GPIO.output(17, False)
#GPIO.output(11, False)
#GPIO.output(12, False)
#GPIO.output(13, False)
#GPIO.output(15, False)
#GPIO.output(16, False)
#GPIO.output(22, False)
GPIO.output(23, False)
GPIO.output(24, False)

pin = { '4' : False , '17' : False , '23' : False, '24' : False}

updateFlag = False

now = datetime.datetime.now()
timeString = now.strftime("%Y-%m-%d %H:%M")

@app.route("/dashboard")
def dashboard():
    sensorName = request.args.get('sensorName')
    dateAgo = request.args.get('dateAgo')
    if (sensorName is None):
        sensorName = "StudyRoom01"
    if (dateAgo is None):
        dateAgo = 1
    dateFrom = now - datetime.timedelta(int(dateAgo))
    templateData = {
        'title' : 'IoT Dashboard',
        'sensor_name' : sensorName,
        'date_from' : int(dateFrom.strftime("%s")) * 1000,
        'time': timeString
    }
    return render_template('dashboard.html', **templateData)
    
@app.route("/")
#@cross_origin()
def hello():
    return dashboard()

@app.route("/api/getIOStatus")
def getIoStatus():
    return json.dumps(pin)

@app.route("/api/getIOStatusAsync")
def getIoStatusAsync():
    while (not updateFlag):
        time.sleep(0.1)
    return json.dumps(pin)

@app.route("/api/moonstar/on")
def apiMoonStaron():
    GPIO.output(17, True)
    message = "GPIO 17 turned on."
    pin['17'] = True
    data = {"message": message, "result": True}
    return json.dumps(data)

@app.route("/api/moonstar/off")
def apiMoonStaroff():
    GPIO.output(17, False)
    message = "GPIO 17 turned off."
    pin['17'] = False
    data = {"message": message, "result": True}
    return json.dumps(data)

@app.route("/api/get/moonstar")
def getMoonStar():
    data = {"pinno" : 17, "output": pin['17']}
    return json.dumps(data)
         
@app.route("/api/heater/on")
def apiHeateron():
    GPIO.output(23, True)
    message = "GPIO 23 turned on."
    pin['23'] = True
    data = {"message": message, "result": True}
    return json.dumps(data)

@app.route("/api/heater/off")
def apiHeateroff():
    GPIO.output(23, False)
    message = "GPIO 23 turned off."
    pin['23'] = False
    data = {"message": message, "result": True}
    return json.dumps(data)

@app.route("/api/get/heater")
def getHeater():
    data = {"pinno" : 23, "output": pin['23']}
    return json.dumps(data)
         
@app.route("/api/humier/on")
def apiHumierOn():
    GPIO.output(24, True)
    message = "GPIO 24 turned on."
    pin['24'] = True
    data = {"message": message, "result": True}
    return json.dumps(data)

@app.route("/api/humier/off")
def apiHumieroff():
    GPIO.output(24, False)
    message = "GPIO 24 turned off."
    pin['24'] = False
    data = {"message": message, "result": True}
    return json.dumps(data)

@app.route("/api/get/humier")
def getHumier():
    data = {"pinno" : 24, "output": pin['24']}
    return json.dumps(data)

@app.route("/api/get/photo")
def readPhoto():
    reading = 0
    GPIO.setup(22, GPIO.OUT)
    GPIO.output(22, GPIO.LOW)
    time.sleep(0.05)
    GPIO.setup(22, GPIO.IN)
    # This takes about 1 millisecond per loop cycle
    while (GPIO.input(22) == GPIO.LOW):
        reading += 1
    data = {"pinno" : 22, "output": reading}
    return json.dumps(data)

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=80, debug=True, threaded=True)
    except KeyboardInterrupt:
        GPIO.cleanup()
        print "GPIO pins cleaned up due to KeyboardInterrupt"
    finally:
        GPIO.cleanup()
        print "GPIO pins cleaned up"
