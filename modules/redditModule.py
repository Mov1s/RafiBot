from ircBase import *
import httplib
import urllib2
import re
from urlparse import urlparse
from bs4 import BeautifulSoup

redditConnection = httplib.HTTPConnection('www.reddit.com')
lastPostedLink = ''

#Get a link from the body of the message, as long as the link is not from reddit
def getLink(message):
	if message:
		link = bodyOfMessage(message)
		if link:
			url = urlparse(link)
			if url.scheme == 'http' and url.netloc != 'www.reddit.com':
				return link
	return None

def main(irc):
	message = irc.lastMessage()

	#Check all posted links for reddit comments
	link = getLink(message)
	if link:
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
				irc.sendMessage("Comments at " + commentLink)
		except:
			return

	#If no room activity for 10 mins link the top rated carPorn picture if it hasn't already been linked
	if noRoomActivityForTime(irc, 600):
		try:
			urlFormat = '/r/carporn'
			redditConnection.request('GET', urlFormat)
			responseBody = redditConnection.getresponse()
			responseBodyString = responseBody.read()

			#Find all of the links
			soup = BeautifulSoup(responseBodyString)
			anchors = soup.find_all('a', "title")

			#Show the top link if it hasn't already been posted
			global lastPostedLink
			topRedditLink = anchors[0]['href']
			if topRedditLink != lastPostedLink:
				lastPostedLink = topRedditLink
				irc.sendMessage(topRedditLink)
		except:
			#Recreate the reddit connection, this should only happen in a timeout
			global redditConnection
			redditConnection = httplib.HTTPConnection('www.reddit.com')