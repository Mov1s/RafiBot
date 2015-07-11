from ircBase import *
import urllib2
from urlparse import urlparse
from bs4 import BeautifulSoup

lastPostedLink = ''

@respondtoregex('(source|src)( me| ma)? (.*)')
def srcMaResponse(aMessage, **extraArgs):
  sourceQuery = extraArgs['match_group'][2]
  commentLink = None
  if sourceQuery:
    if aMessage.has_links:
      commentLink = getRedditCommentsForLink(aMessage.links[0])
    else:
      for logMessage in reversed(IrcBot.shared_instance().message_log):
        if logMessage.has_links:
          commentLink = getRedditCommentsForLink(logMessage.links[0])
          break
    response = "Comments at " + commentLink if commentLink else "No source found"
    return aMessage.new_response_message(response)

@respondtoidletime(300)
def idleCarPornResponse(**extraArgs):
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
    topRedditLink = anchors[1]['href']
    if topRedditLink != lastPostedLink:
      lastPostedLink = topRedditLink
      return IrcMessage.new_room_message(topRedditLink)
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

