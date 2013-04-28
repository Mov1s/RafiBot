# -*- coding:utf8 -*-
from ircBase import *
import urllib2
import urllib
from bs4 import BeautifulSoup


def getQuery(message):
	expression = re.compile('(temperature|temp)( me| ma)? (.*)', re.IGNORECASE)
	match = expression.match(message)
	if match:
		return match.group(3)
	else:
		return None	

def main(irc):
 	message = irc.lastMessage()
	
	if message.body != None:
		query = getQuery(message.body)
		#Temperature command
		if query:
			try:
				#Request Weather Underground for weather 
				query = query.replace(',', '%2C')
				query = query.replace(' ', '+')
				url = "http://www.wunderground.com/cgi-bin/findweather/hdfForecast?query=" + query 
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

				newMessage = ircMessage().newRoomMessage("It is " + temperatureSpan.string + "F and " + currentCondition.string + ", Feels Like " + feelsLike.string + "F in " + locationName.string)
				irc.sendMessage(newMessage)
			except:
				return
