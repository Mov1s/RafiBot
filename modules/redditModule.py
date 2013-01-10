from ircBase import *
import urllib2
import re
from urlparse import urlparse
from bs4 import BeautifulSoup

lastPostedLink = ''

#Check if a message is requesting the source of a link
def getSourceQuery(message):
	expression = re.compile('(source|src)( me| ma)? (.*)', re.IGNORECASE)
	match = expression.match(message)
	if match:
		return match.group(3)
	else:
		return None

#Searches reddit for a specific link and returns the comments if any are found
def getRedditCommentsForLink(link):
	try:
		#Search reddit for this link
		link = link.replace(':', '%3A').replace('/', '%2F')
		url = "http://www.reddit.com/submit?url=" + link
		request = urllib2.Request(url)
		request.add_header('User-agent', 'Mozilla/5.0')
		response = urllib2.urlopen(request)
		responseBodyString = response.read()

		#Find all of the links
		soup = BeautifulSoup(responseBodyString)
		anchors = soup.find_all('a', "comments")
		if len(anchors) >= 1:
			commentLink = anchors[0]['href']
			return commentLink
	except:
		return None

def main(irc):
	message = irc.lastMessage()

	#Return reddit comments for a link if provided
	#If no link provided return comments for last posted link
	if not message.body == None:
		commentLink = None
		sourceQuery = getSourceQuery(message.body)
		if sourceQuery:
			if message.hasLinks:
				commentLink = getRedditCommentsForLink(message.links[0])
			else:
				for logMessage in reversed(irc.messageLog):
					if logMessage.hasLinks:
						commentLink = getRedditCommentsForLink(logMessage.links[0])
			if commentLink:
				irc.sendMessageToRoom("Comments at " + commentLink)
			else:
				irc.sendMessageToRoom("No source found")

	#If no room activity for 10 mins link the top rated carPorn picture if it hasn't already been linked
	if noRoomActivityForTime(irc, 600):
		try:
			urlFormat = '/r/carporn'
			url = 'http://www.reddit.com' + urlFormat
			response = urllib2.urlopen(url)
			responseBodyString = response.read()

			#Find all of the links
			soup = BeautifulSoup(responseBodyString)
			anchors = soup.find_all('a', "title")

			#Show the top link if it hasn't already been posted
			global lastPostedLink
			topRedditLink = anchors[0]['href']
			if topRedditLink != lastPostedLink:
				lastPostedLink = topRedditLink
				irc.sendMessageToRoom(topRedditLink)
		except:
			return

