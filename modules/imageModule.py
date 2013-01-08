from ircBase import *
import httplib
import json
import re
from random import randint

googleAPI = 'ajax.googleapis.com'
googleURI = httplib.HTTPConnection(googleAPI)
uriFormat = '/ajax/services/search/images?v=1.0&rsz=8&q='

def imageMe(query):
  try:
    googleURI.request('GET', uriFormat + query)
    response = googleURI.getresponse()
    responseString = response.read()
    responseJSON = json.loads(responseString)
    length = len(responseJSON['responseData']['results'])
    if length > 0:
      image = responseJSON['responseData']['results'][randint(0, length - 1)]['unescapedUrl']
      return image
  except:
    global googleURI
    googleURI = httplib.HTTPConnection(googleAPI)

def getQuery(message):
  expression = re.compile(':(image|img)( me)? (.*)', re.IGNORECASE)
  match = expression.search(message)
  if match:
    return match.group(3)
  else:
    return None

def main(irc):
  message = irc.lastMessage()
  if message:
    query = getQuery(message)
    if query:
      result = imageMe(query)
      if result:
        irc.sendMessage(result)
      else:
        irc.sendMessage('Nothing found for ' + query)