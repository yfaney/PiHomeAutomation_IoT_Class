# This is for Weather Underground API
import urllib2, json

REQUEST_URL_HOME = "http://api.wunderground.com"
API_KEY = "1311abfeb457472a" # Hayden's key

def getHourlyFC(zipcode):
    url = "%s/api/%s/hourly/q/%s.json" % (REQUEST_URL_HOME, API_KEY, str(zipcode                                      ))
    respJson = requestWUG(url)
    return respJson

def getHourlyFC_HTSensor(zipcode):
    respJson = getHourlyFC(zipcode)
    forecastJson = respJson['hourly_forecast']
    newFormat = []
    for item in forecastJson:
        hourly = {}
        hourly['epoch'] = item['FCTTIME']['epoch']
        hourly['temp'] = item['temp']['metric']
        hourly['humidity'] = item['humidity']
        newFormat.append(hourly)
    return newFormat

def getHourlyForecast(zipcode, unit):
    respJson = getHourlyFC(zipcode)
    forecastJson = respJson['hourly_forecast']
    newFormat = []
    for item in forecastJson:
        hourly = {}
        hourly['epoch'] = item['FCTTIME']['epoch']
        if(unit == "english"):
            hourly['temp'] = item['temp']['english']
        else:
            hourly['temp'] = item['temp']['metric']
        hourly['humidity'] = item['humidity']
        newFormat.append(hourly)
    return newFormat

def requestWUG(url):
    errorCount = 10
    while errorCount > 0:
        #response = requests.get(url)
        resp = urllib2.urlopen(url)
        #str_response = response.text.decode('utf-8')
        str_response = resp.read().decode('utf-8')
        obj = json.loads(str_response)
        if 'error' in obj['response']:
            print("Error in retrieving data. Trying again...")
            logging.error("DataRetrievalError - TWC API Error")
            # Retrying after 1 sec
            time.sleep(1)
        else:
            errorCount = 0
    return obj
