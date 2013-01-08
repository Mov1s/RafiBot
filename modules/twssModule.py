from ircBase import *
import urllib2
import urllib
from bs4 import BeautifulSoup

def main(irc):
	message = irc.lastMessage()

	#Don't check for messages that aren't for the room
	#This also filters out things said by Rafi, so it only looks at other nicks messages'
	if not messageIsForRoom(message):
		return

	try:
		#Request TWSS for a given message
		twss = bodyOfMessage(message).replace(' ', '+')
		url = "http://twss-classifier.heroku.com/?sentence=" + twss
		responseBodyString = urllib2.urlopen(url).read()

		#Find TWSS span
		soup = BeautifulSoup(responseBodyString)
		twssSpan = soup.find("span", {"id": "twss"})

		#Check if that's what she said
		if twssSpan.string == "That's what she said!":
			irc.sendMessage("That's what she said!")
	except:
		return