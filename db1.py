import requests
import json
import xml
import datetime
from xml.dom import minidom
import xml.etree.ElementTree as ET
import codes

class Train:
        delay = 0
        delayCode = 0

        def setDelayReason(self, code):
            self.delayCode = code

        def setDelay(self, delay):
            self.delay = delay

        def __init__(self, id, time, line, destination, platform, nextStations):
            self.id = id
            self.time = int(time)
            self.line = line
            self.destination = destination
            self.platform = platform
            self.nextStations = nextStations

def addZero(str):
    if len(str) == 1:
        return "0"+str
    else:
        return str


def getDifferenceInMinutes(a, b):
    if int(str(a)[0:2]) < int(str(b)[0:2]):
        b = b-40 
    return b-a


def getData():
    now = datetime.datetime.now()

    # API-Token 
    api_token = 'YOUR_API_KEY'
    headers = {#'Content-Type': 'application/xml',
               'Authorization': 'Bearer {0}'.format(api_token)}

    h = now.hour
    d = now.day
    m = now.month
    y = now.year

    h1 = h+1
    h2 = h+2
    d1 = d
    d2 = d
    m1 = m
    m2 = m

    if m%2 != 0:
        maxD = 31
    else:
        maxD = 30

    maxH = 23

    if h1 == 24 and h == 23:
        h1 = 0
        d1 = d+1

    if h2 == 24 and h == 22:
        h2 = 0
        d2 = d+1

    if h2 == 25 and h == 23:
        h2 = 1

    # Station-ID Boeblingen: 8001055

    # API for planned departures and train information (current hour)
    url_train_information_now = 'https://api.deutschebahn.com/timetables/v1/plan/8005201/'
    url_train_information_now = url_train_information_now + addZero(str(y))[2:4] + addZero(str(m)) + addZero(str(d)) + '/' + addZero(str(h))
    url_train_information_now = '{0}'.format(url_train_information_now)
    print(url_train_information_now)

    # API for planned departures and train information (next hour)
    url_train_information_hourlater = 'https://api.deutschebahn.com/timetables/v1/plan/8005201/'
    url_train_information_hourlater = url_train_information_hourlater + addZero(str(y))[2:4] + addZero(str(m1)) + addZero(str(d1)) + '/' + addZero(str(h1))
    url_train_information_hourlater = '{0}'.format(url_train_information_hourlater)
    print(url_train_information_hourlater)

    # API for planned departures and train information (+2 hours)
    url_train_information_twohourlater = 'https://api.deutschebahn.com/timetables/v1/plan/8005201/'
    url_train_information_twohourlater = url_train_information_twohourlater + addZero(str(y))[2:4] + addZero(str(m2)) + addZero(str(d2)) + '/' + addZero(str(h2))
    url_train_information_twohourlater = '{0}'.format(url_train_information_twohourlater)
    print(url_train_information_twohourlater)




    # API for train information (current + next hour)
    responseTrainInfoNow = requests.get(url_train_information_now, headers=headers)
    xmlTrainInfoNow = responseTrainInfoNow.text

    responseTrainInfoHourLater = requests.get(url_train_information_hourlater, headers=headers)
    xmlTrainInfoHourLater = responseTrainInfoHourLater.text

    responseTrainInfoTwoHourLater = requests.get(url_train_information_twohourlater, headers=headers)
    xmlTrainInfoTwoHourLater = responseTrainInfoTwoHourLater.text

    root = ET.fromstring(xmlTrainInfoNow)
    trainsXML = root.findall('s')

    rootHourLater = ET.fromstring(xmlTrainInfoHourLater)
    trainsXML.extend(rootHourLater.findall('s'))

    rootTwoHourLater = ET.fromstring(xmlTrainInfoTwoHourLater)
    trainsXML.extend(rootTwoHourLater.findall('s'))

    trains = []

    for t in trainsXML:
        id = t.attrib.get('id')
        tl = t.find('tl')
        ar = t.find('ar')
        dp = t.find('dp')
    
        # Train Line
        try:
            line = tl.get('f') + ar.get('l')
        except AttributeError:
            line = "404"
        except TypeError:
            line = "404"

        # Time
        try:
            time = ar.get('pt')
            time = time[6:10]
        except AttributeError:
            time = "404"

        # Plate
        try:
            platform = ar.get('pp')
        except AttributeError:
            platform = "0"

        # Next Stations
        try:
            nextStationsTxt = dp.get('ppth')
            nextStations = nextStationsTxt.split('|')
        except AttributeError:
            nextStations = ["unknown","error"]
    
        # Destination
        destination = nextStations[len(nextStations)-1]

        train = Train(id, time, line, destination, platform, nextStations)
        trains.append(train)

    # API for information about the delay reason
    url_realtime_info = 'https://api.deutschebahn.com/timetables/v1/fchg/8005201'
    url_realtime_info = '{0}'.format(url_realtime_info)

    responseRealtimeInfo = requests.get(url_realtime_info, headers=headers)
    xmlRealtimeInfo = responseRealtimeInfo.text

    root = ET.fromstring(xmlRealtimeInfo)
    trainsRT = root.findall('s')

    for t in trainsRT:
        id = t.get('id')
        ar = t.find('ar')
        dp = t.find('dp')
        try:
            m = ar.find('m')
            try:
                time = ar.get('ct')[6:10]
            except TypeError:
                time = 0
        except AttributeError:
            print("cannot find meta tag")

        delayCode = 0

        if m != None:  
            try:
                delayCode = m.get('c')
            except AttributeError:
                delayCode = 0
        else:
            delayCode = 0

        for i in range(0, len(trains)):
            if trains[i].id == id:
                trains[i].setDelayReason(int(delayCode))
                trains[i].setDelay(getDifferenceInMinutes(int(trains[i].time), int(time)))
                if trains[i].delay < 0:
                    trains[i].delay = 0
            
    trainsFiltered = []

    for i in range(0, len(trains)):
        if trains[i].time >= int(str(addZero(str(now.hour)))+str(addZero(str(now.minute)))) and trains[i].destination != "error" and trains[i].line != "404":
            print(str(trains[i].time) + " +"+str(trains[i].delay)+" "+trains[i].line+" "+trains[i].destination+" "+str(trains[i].delayCode)+" "+codes.codes[trains[i].delayCode])
            trainsFiltered.append(trains[i])

    def formattime(timee):
        if len(str(timee)) == 1:
            return "00:0"+str(timee)
        if len(str(timee)) == 2:
            return "00:"+str(timee)
        if len(str(timee)) == 3:
            return "0"+str(timee)[0:1]+":"+str(timee)[1:3]
        if len(str(timee)) == 4:
            return str(timee)[0:2]+":"+str(timee)[2:4]
        else:
            return -1

    trainsFiltered.sort(key=lambda x: x.time)

    str2 = ""
    for i in range(0, len(trainsFiltered)):
        if len(str(codes.codes[trainsFiltered[i].delayCode])) == 0:
            print("NichtMeldung: "+str(trainsFiltered[i].time) + " "+str(trainsFiltered[i].delayCode)+" #"+str(codes.codes[trainsFiltered[i].delayCode])+"#")
            if trainsFiltered[i].delay == 0:
                str2 = str2+"<tr><td class=\"Zeit\">"+ formattime(str(trainsFiltered[i].time)) + "</td><td class=\"Verspatung\">" + "</td><td class=\"Placeholder\"></td><td class=\"SBahn\">" + str(trainsFiltered[i].line) + "</td><td class=\"Uber\">"+trainsFiltered[i].nextStations[0]+"</td><td class=\"Ziel\">" + trainsFiltered[i].destination + "</td><td class=\"Gleis\">"+trainsFiltered[i].platform+"</td><td class=\"NichtMeldung\">" + codes.codes[trainsFiltered[i].delayCode] + "</td></tr>"
            else:
                str2 = str2+"<tr><td class=\"Zeit\">"+ formattime(str(trainsFiltered[i].time)) + "</td><td class=\"Verspatung\">      +" + str(trainsFiltered[i].delay) + "</td><td class=\"Placeholder\"></td><td class=\"SBahn\">" + str(trainsFiltered[i].line) + "</td><td class=\"Uber\">"+trainsFiltered[i].nextStations[0]+"</td><td class=\"Ziel\">" + trainsFiltered[i].destination + "</td><td class=\"Gleis\">"+trainsFiltered[i].platform+"</td><td class=\"NichtMeldung\">" + codes.codes[trainsFiltered[i].delayCode] + "</td></tr>"
        else:
            print("     Meldung: "+str(trainsFiltered[i].time) + " "+str(trainsFiltered[i].delayCode)+" #"+str(codes.codes[trainsFiltered[i].delayCode])+"#")
            str2 = str2+"<tr><td class=\"Zeit\">"+ formattime(str(trainsFiltered[i].time)) + "</td><td class=\"Verspatung\">+" + str(trainsFiltered[i].delay) + "</td><td class=\"Placeholder\"></td><td class=\"SBahn\">" + str(trainsFiltered[i].line) + "</td><td class=\"Uber\">"+trainsFiltered[i].nextStations[0]+"</td><td class=\"Ziel\">" + trainsFiltered[i].destination + "</td><td class=\"Gleis\">"+trainsFiltered[i].platform+"</td><td class=\"Meldung\">" + codes.codes[trainsFiltered[i].delayCode] + "</td></tr>"
             
    str2 = str2+"</td>"

    return str2
    
print(getData())