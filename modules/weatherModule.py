# -*- coding:utf8 -*-
from ircBase import *
import urllib2
import urllib
import ConfigParser
import json

config = ConfigParser.SafeConfigParser()
config.read('configs/weatherModule.conf')

CONST_API_KEY = config.get('WeatherModule', 'apiKey')
CONST_RADAR_ZOOM = config.get('WeatherModule', 'radarZoom')

@respondtoregex('(temperature|temp)( me| ma)? (.*)')
def currentCondition(message, **extra_args):
	#Request Weather Underground for weather
	query = extra_args['match_group'][2]
	query = query.replace(',', '%2C')
	query = query.replace(' ', '+')
	url = "http://api.wunderground.com/api/" + CONST_API_KEY + "/geolookup/conditions/q/" + query + ".json"
	f = urllib2.urlopen(url)
	json_string = f.read()
	parsed_json = json.loads(json_string)
	try:
		location = parsed_json['current_observation']['display_location']['full']
		temp_f = parsed_json['current_observation']['temp_f']
		feelslike_f = parsed_json['current_observation']['feelslike_f']
		weather = parsed_json['current_observation']['weather']

		response = "It is " + str(temp_f) + "F and " + weather + ", Feels Like " + str(feelslike_f) + "F in " + location
		return message.new_response_message(response)
	except:
		response = "Multiple results returned; please use a more specific search string."
		return message.new_response_message(response)

@respondtoregex('(radar|rad)( me| ma)? (.*)')
def wunderMap(message, **extra_args):
    #Request Weather Underground for weather
    query = extra_args['match_group'][2]
    query = query.replace(',', '%2C')
    query = query.replace(' ', '+')
    url = "http://api.wunderground.com/api/" + CONST_API_KEY + "/geolookup/conditions/q/" + query + ".json"
    f = urllib2.urlopen(url)
    json_string = f.read()
    parsed_json = json.loads(json_string)
    try:
        location = parsed_json['current_observation']['display_location']['full']
        longitude = parsed_json['current_observation']['display_location']['longitude']
        latitude = parsed_json['current_observation']['display_location']['latitude']

        print location
        print longitude
        print latitude
        location = location.replace(',', '%2C')
        location = location.replace(' ', '+')

        response = "http://www.wunderground.com/wundermap/?lat=" + latitude + "&lon=" + longitude + "&zoom=" + CONST_RADAR_ZOOM + "&pin=" + location + "&rad=1"
        return message.new_response_message(response)
    except:
        response = "Multiple results returned; please use a more specific search string."
        return message.new_response_message(response)


@respondtoregex('(forecast|fore)( me| ma)? (.*)')
def forecast(message, **extra_args):
	#Request Weather Underground for weather
	query = extra_args['match_group'][2]
	query = query.replace(',', '%2C')
	query = query.replace(' ', '+')
	url = "http://api.wunderground.com/api/" + CONST_API_KEY + "/geolookup/forecast/q/" + query + ".json"
	f = urllib2.urlopen(url)
	json_string = f.read()
	parsed_json = json.loads(json_string)
	messages = []

	try:
		for days, item in enumerate(parsed_json['forecast']['txt_forecast']['forecastday']):
			day = item['title']
			conditions = item['fcttext']

			messages.append(IrcMessage.new_private_message(day + ": " + conditions, message.sending_nick, off_record = True))

		return messages
	except:
		messages.append(IrcMessage.new_private_message("Multiple results returned; please use a more specific search string.", message.sending_nick, off_record = True))
		return messages
