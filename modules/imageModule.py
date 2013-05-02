from ircBase import *
import urllib2
import json
import re
from random import randint

googleAPI = 'http://ajax.googleapis.com'
uriFormat = '/ajax/services/search/images?v=1.0&rsz=8&q='

def imageMe(query):
  try:
    query = query.replace(' ', '+')
    url = googleAPI + uriFormat + query
    response = urllib2.urlopen(url)
    responseString = response.read()
    responseJSON = json.loads(responseString)
    length = len(responseJSON['responseData']['results'])
    if length > 0:
      image = responseJSON['responseData']['results'][randint(0, length - 1)]['unescapedUrl']
      return image
  except:
    return None

def getQuery(message):
  expression = re.compile('(image|img)( me| ma)? (.*)', re.IGNORECASE)
  match = expression.match(message)
  if match:
    return match.group(3)
  else:
    return None

def main(irc):
  message = irc.lastMessage()
  messages = []
  if message.body != None:
    query = getQuery(message.body)
    if query:
      result = imageMe(query)
      if result:
        messages.append(IrcMessage.newRoomMessage(result))
      else:
        messages.append(IrcMessage.newRoomMessage('Nothing found for ' + query))
  irc.sendMessages(messages)