from ircBase import *
import urllib2
import urllib
from bs4 import BeautifulSoup

def main(irc):
	message = irc.lastMessage()

	try:
		#Request TWSS for a given message
		twssMessage = message[message.rfind(':') + 1:].replace(' ', '+')
		url = "http://twss-classifier.heroku.com/?sentence=" + twssMessage
		responseBodyString = urllib2.urlopen(url).read()

		#Find TWSS span
		soup = BeautifulSoup(responseBodyString)
		twssSpan = soup.find("span", {"id": "twss"})

		#Check if that's what she said
		if twssSpan.string == "That's what she said!":
			irc.sendMessage("That's what she said!")
	except:
		return