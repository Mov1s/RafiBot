from ircBase import *
import urllib2
import urllib
from bs4 import BeautifulSoup

@respondtoregex('.*')
def twss_response(message, **extra_args):

	#Don't check for messages that arent room messages or pms
	#This also filters out things said by Rafi, so it only looks at other nicks messages'
	if message.is_private_message or (message.is_room_message and message.sending_nick != IrcBot.shared_instance().nick):
		try:
			#Request TWSS for a given message
			twss = message.body.replace(' ', '+')
			url = "http://twss-classifier.heroku.com/?sentence=" + twss
			responseBodyString = urllib2.urlopen(url).read()

			#Find TWSS span
			soup = BeautifulSoup(responseBodyString)
			twssSpan = soup.find("span", {"id": "twss"})

			#Check if that's what she said
			if twssSpan.string == "That's what she said!":
				return message.new_response_message("That's what she said!")
		except:
			return
