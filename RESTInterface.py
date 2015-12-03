import urllib2, httplib, json, csv
from datetime import timedelta, date, datetime, time
import pytz

DB_URL = "http://localhost:27018"
SUB_HT_SENSOR = "/iot/ht_sensor"
SUB_HT_FORECAST = "/iot/ht_forecast"
SUB_GCM_KEYS = "/iot/gcm_keys"
ZIPCODE_CSV = "zip_code_database.csv"
CURRENT_TZONE = "America/Chicago"

GPIO_API_URL = "http://localhost"
SUB_API_HEATER = "/api/heater"
SUB_API_HUMIER = "/api/humier"
SUB_API_LIGHT = "/api/moonstar"
SUB_API_PHOTO = "/api/get/photo"


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def to_epoch(pdate):
    return int(pdate.strftime("%s")) * 1000

def auto_convert_string_to_number(json):
    if(isinstance(json, list)):
        newJsons = []
        for item in json:
            newJsons.append(auto_convert_string_to_number(item))
        return newJsons
    else:
        newJson = {}
        try:
            for key in list(json):
                if(isinstance(json[key], dict)):
                    newJson[key] = auto_convert_string_to_number(json[key])
                else:
                    newJson[key] = num(json[key])
            return newJson
        except:
            return json

def num(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except:
            return s

class gpioInterface:
    def __init__(self, p_root):
        self.root = p_root
    def heater_onoff(self, onoff):
        if(onoff):
            url = self.root  + SUB_API_HEATER + "/on"
        else:
            url = self.root  + SUB_API_HEATER + "/off"
        req = urllib2.urlopen(url)
        resp = req.read()
        return resp
    def humier_onoff(self, onoff):
        if(onoff):
            url = self.root  + SUB_API_HUMIER + "/on"
        else:
            url = self.root  + SUB_API_HUMIER + "/off"
        req = urllib2.urlopen(url)
        resp = req.read()
        return resp
    def light_onoff(self, onoff):
        if(onoff):
            url = self.root  + SUB_API_LIGHT + "/on"
        else:
            url = self.root  + SUB_API_LIGHT + "/off"
        req = urllib2.urlopen(url)
        resp = req.read()
        return resp
    def get_photo_sensor(self):
        url = self.root  + SUB_API_PHOTO
        req = urllib2.urlopen(url)
        resp = req.read()
        return resp
        

class dbInterface:
    def __init__(self):
        self.zipDB = zipcodeDB()
        
    def post_ht_sensor(self, sensor_name, date, temp, humi, msg):
        epoch = to_epoch(date)
        post_data = json.dumps({"sensor_name":sensor_name, "tstamp":{"$date":epoch}, "temperature":temp, "humidity":humi, "message":msg})
        #print post_data
        req = urllib2.urlopen(DB_URL + SUB_HT_SENSOR, post_data)
        resp = req.read()
        return resp
	
    def post_ht_forecast(self, epoch, zipcode, temp, humi):
        post_data = json.dumps({"zipcode":zipcode, "tstamp":{"$date":epoch}, "temperature":float(temp), "humidity":float(humi)})
        #print post_data
        req = urllib2.urlopen(DB_URL + SUB_HT_FORECAST, post_data)
        resp = req.read()
        return resp

    def get_ht_sensor(self, date_from, date_to, sensor_name):
        epoch_from = to_epoch(date_from)
        epoch_to = to_epoch(date_to)
        url = '%s%s?query={"tstamp":{"$gte":{"$date":%d},"$lte":{"$date":%d}},"sensor_name":"%s"}'%(DB_URL, SUB_HT_SENSOR, epoch_from, epoch_to, sensor_name)
        req = urllib2.urlopen(url)
        return json.loads(req.read())

    def get_ht_sensor_tstamp(self, single_time, sensor_name):
        epoch_date = to_epoch(single_time)
        url = '%s%s?query={"tstamp":{"$date":%d},"zipcode":"%s"}'%(DB_URL, SUB_HT_SENSOR, epoch_date, sensor_name)
        req = urllib2.urlopen(url)
        return json.loads(req.read())

    def get_ht_sensor_bydate(self, lDate, sensor_name):
        date_from = datetime(lDate.year, lDate.month, lDate.day, 0, 0, 0,0)
        date_to = datetime(lDate.year, lDate.month, lDate.day, 23, 59, 59, 999)
        return self.get_ht_sensor(date_from, date_to, sensor_name)

    def get_ht_forecast(self, date_from, date_to, zipcode):
        tzone = pytz.timezone(self.zipDB.get_timezone(zipcode))
        try:
            localized_from = tzone.localize(date_from)
            localized_to = tzone.localize(date_to)
        except Exception, e:
            print (str(e))
            localized_from = tzone.localize(datetime.combine(date_from, time.min))
            localized_to = tzone.localize(datetime.combine(date_to, time.max))
        epoch_from = to_epoch(localized_from)
        epoch_to = to_epoch(localized_to)
        url = '%s%s?query={"tstamp":{"$gte":{"$date":%d},"$lte":{"$date":%d}},"zipcode":"%s"}'%(DB_URL, SUB_HT_FORECAST, epoch_from, epoch_to, zipcode)
        req = urllib2.urlopen(url)
        return json.loads(req.read())

    def get_ht_forecast_tstamp(self, single_time, zipcode):
        tzone = pytz.timezone(self.zipDB.get_timezone(zipcode))
        localized_date = tzone.localize(single_time)
        epoch_date = to_epoch(localized_date)
        url = '%s%s?query={"tstamp":{"$date":%d},"zipcode":"%s"}'%(DB_URL, SUB_HT_FORECAST, epoch_date, zipcode)
        req = urllib2.urlopen(url)
        return json.loads(req.read())

    def get_gcm_keys(self):
        url = '%s%s?fields={"_id":0}'%(DB_URL, SUB_GCM_KEYS)
        req = urllib2.urlopen(url)
        return json.loads(req.read())

    def delete_ht_sensor(self, date_from, date_to, sensor_name):
        suburl = '%s?query={"tstamp":{"$gte":{"$date":%d},"$lte":{"$date":%s}},"sensor_name":"%s"}'%(SUB_HT_SENSOR, to_epoch(date_from),to_epoch(date_to),sensor_name)
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(DB_URL + suburl)
        req.get_method = lambda: 'DELETE'
        resp = urllib2.urlopen(req)
        return json.loads(resp.read())

    def delete_ht_forecast(self, date_after, zipcode):
        epoch_before = to_epoch(date_after)
        suburl = '%s?query={"tstamp":{"$gte":{"$date":%d}},"zipcode":"%s"}'%(SUB_HT_FORECAST, epoch_before, zipcode)
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(DB_URL + suburl)
        req.get_method = lambda: 'DELETE'
        resp = urllib2.urlopen(req)
        return json.loads(resp.read())

    def to_localized_epoch(self, date, zipcode):
        tzone = pytz.timezone(self.zipDB.get_timezone(zipcode))
        try:
            localized = tzone.localize(date)
        except Exception, e:
            print (str(e))
            localized = tzone.localize(datetime.combine(date, time.min))
        return to_epoch(localized)

    def to_localized_datetime(self, date, zipcode):
        tzone = pytz.timezone(self.zipDB.get_timezone(zipcode))
        try:
            localized = tzone.localize(date)
        except Exception, e:
            print (str(e))
            localized = tzone.localize(datetime.combine(date, time.min))
        return localized

    def to_utc_datetime(self, date, zipcode):
        epoch = to_epoch(date)
        utc_dt = pytz.utc.localize(datetime.utcfromtimestamp(epoch / 1000))
        return utc_dt

    def epoch_to_localized(self, epoch, zipcode):
        tzone = pytz.timezone(self.zipDB.get_timezone(zipcode))
        utc_dt = pytz.utc.localize(datetime.utcfromtimestamp(epoch / 1000))
        return tzone.normalize(utc_dt)

    def epoch_to_utc(self, epoch, zipcode):
        utc_dt = pytz.utc.localize(datetime.utcfromtimestamp(epoch / 1000))
        return utc_dt

class zipcodeDB:
    def __init__(self):
        self.zipDB = []
        with open(ZIPCODE_CSV, 'r') as csvfile:
            raw = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in raw:
                self.zipDB.append(row)

    def get_timezone(self, zipcode):
        for row in self.zipDB:
            if(row[0] == zipcode):
                return row[7]

