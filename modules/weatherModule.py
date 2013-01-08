from ircBase import *
import urllib2
import urllib
from bs4 import BeautifulSoup
python string concatenation
def main(irc):
  message = irc.lastMessage()

	#Temperature command
	if messageIsBotCommand(message, 'temperature'):
		return

	try:
		#Request Weather Underground for temperature
		temperature = message[message.rfind('temperature') + 1:].replace(' ', '+')
		temperature = temperature.replace(',', '%2C')
		url = "http://www.wunderground.com/cgi-bin/findweather/hdfForecast?query=" + temperature
		responseBodyString = urllib2.urlopen(url).read()

		#Find Current Temperature Span
		soup = BeautifulSoup(responseBodyString)
		temperatureSpan = soup.find("span", {"id": "rapidtemp"})
		feelsLike = soup.find("div", {"id": "tempFeel"})

		irc.sendMessage(temperatureSpan + ' °F ' + feelsLike)
	except:
		return
