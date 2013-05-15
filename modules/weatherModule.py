# -*- coding:utf8 -*-
from ircBase import *
import urllib2
import urllib
from bs4 import BeautifulSoup
import ConfigParser
import json

config = ConfigParser.SafeConfigParser()
config.read('configs/weatherModule.conf')

CONST_API_KEY = config.get('WeatherModule', 'apikey')


def getTemperatureQuery(message):
	expression = re.compile('(temperature|temp)( me| ma)? (.*)', re.IGNORECASE)
	match = expression.match(message)
	if match:
		return match.group(3)
	else:
		return None	

def getForecastQuery(message):
	expression = re.compile('(forcase|fore)( me| ma)? (.*)', re.IGNORECASE)
	match = expression.match(message)
	if match:
		return match.group(3)
	else:
		return None	

def currentCondition(query):
	#Request Weather Underground for weather 
	query = query.replace(',', '%2C')
	query = query.replace(' ', '+')
	url = "http://api.wunderground.com/api/" + CONST_API_KEY + "/geolookup/conditions/q/" + query + ".json" 
	print(url)
	f = urllib2.urlopen(url)
	json_string = f.read()
	parsed_json = json.loads(json_string)
	try:	
		location = parsed_json['current_observation']['display_location']['full']
		temp_f = parsed_json['current_observation']['temp_f']
		feelslike_f = parsed_json['current_observation']['feelslike_f']
		weather = parsed_json['current_observation']['weather']

		message = "It is " + str(temp_f) + "F and " + weather + ", Feels Like " + str(feelslike_f) + "F in " + location
		return message
	except:
		message = "Multiple results returned; please use a more specific search string."	
		return message

def forecast(query):
	#Request Weather Underground for weather 
	query = query.replace(',', '%2C')
	query = query.replace(' ', '+')
	url = "http://api.wunderground.com/api/" + CONST_API_KEY + "/geolookup/forecast/q/" + query + ".json" 
	print(url)
	f = urllib2.urlopen(url)
	json_string = f.read()
	parsed_json = json.loads(json_string)
	try:	
		location = parsed_json['forecast']['display_lecation']['full']
		temp_f = parsed_json['current_observation']['temp_f']
		feelslike_f = parsed_json['current_observation']['feelslike_f']
		weather = parsed_json['current_observation']['weather']

		message = "It is " + str(temp_f) + "F and " + weather + ", Feels Like " + str(feelslike_f) + "F in " + location
		return message
	except:
		message = "Multiple results returned; please use a more specific search string."	
		return message


def main(irc):
 	message = irc.lastMessage()
	
	if message.body != None:
		query = getTemperatureQuery(message.body)
		#Temperature command
		if query:
			newMessage = IrcMessage.newRoomMessage(currentCondition(query))
			irc.sendMessage(newMessage)

		query = getForecastQuery(message.body)
		#Temperature command
		if query:
			newMessage = IrcMessage.newRoomMessage(currentCondition(query))
			irc.sendMessage(newMessage)
