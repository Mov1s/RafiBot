# -*- coding:utf8 -*-
from ircBase import *
import urllib2
import urllib
from bs4 import BeautifulSoup

def main(irc):
  	message = irc.lastMessage()
	
	expression = re.compile('(temperature|temp)(me|ma)? (.*)', re.IGNORECASE)
	match = expression.match(message)

	#Temperature command
	if match:
		try:
			#Request Weather Underground for weather 
			temperature = message.body[message.body.rfind('weather') + 8:].replace(' ', '+')
			temperature = temperature.replace(',', '%2C')
			url = "http://www.wunderground.com/cgi-bin/findweather/hdfForecast?query=" + temperature
			responseBodyString = urllib2.urlopen(url).read()

			soup = BeautifulSoup(responseBodyString)

			#Find Current Temperature Span
			temperatureSpan = soup.find("span", {"id": "rapidtemp"})
			temperatureSpan = temperatureSpan.find("span", {"class": "b"})

			#Find Feels Like Temperature
			feelsLike = soup.find("div", {"id": "tempFeel"})
			feelsLike = feelsLike.find("span", {"class": "b"})

			#Find Current Condition
			currentCondition = soup.find("div", {"id": "curCond"})

			#Find Location
			locationName = soup.find("h1", {"id": "locationName"})
			#locationName = locationName.find("span", {"class": "b"})

			ircMessage().newRoomMessage(irc, "It is " + temperatureSpan.string + "F and " + currentCondition.string + ", Feels Like " + feelsLike.string + "F in " + locationName.string).send()
		except:
			return
