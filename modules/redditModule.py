from ircBase import *
import urllib2
import re
from urlparse import urlparse
from bs4 import BeautifulSoup

lastPostedLink = ''

class RedditModule(IrcModule):
  
  def defineResponses(self):
    self.respondToRegex('(source|src)( me| ma)? (.*)', self.srcMaResponse)
    self.respondToIdleTime(300, self.idleCarPornResponse)

  def srcMaResponse(self, aMessage, **extraArgs):
    sourceQuery = extraArgs['matchGroup'][2]
    commentLink = None
    if sourceQuery:
      if aMessage.hasLinks:
        commentLink = getRedditCommentsForLink(aMessage.links[0])
      else:
        for logMessage in reversed(extraArgs['ircConnection'].messageLog):
          if logMessage.hasLinks:
            commentLink = getRedditCommentsForLink(logMessage.links[0])
            break
      response = "Comments at " + commentLink if commentLink else "No source found"
      return aMessage.newResponseMessage(response)

  def idleCarPornResponse(self, **extraArgs):
    try:
      urlFormat = '/r/carporn'
      url = 'http://www.reddit.com' + urlFormat
      request = urllib2.Request(url)
      request.add_header('User-agent', 'Mozilla/5.0')
      response = urllib2.urlopen(request)
      responseBodyString = response.read()

      #Find all of the links
      soup = BeautifulSoup(responseBodyString)
      anchors = soup.find_all('a', "title")
      
      #Show the top link if it hasn't already been posted
      global lastPostedLink
      topRedditLink = anchors[0]['href']
      if topRedditLink != lastPostedLink:
        lastPostedLink = topRedditLink
        return IrcMessage.newRoomMessage(topRedditLink)
    except:
      return


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

