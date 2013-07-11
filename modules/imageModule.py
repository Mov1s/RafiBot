from ircBase import *
import urllib2
import json
import re
from random import randint

googleAPI = 'http://ajax.googleapis.com'
uriFormat = '/ajax/services/search/images?v=1.0&rsz=8&q='

class ImageModule(IrcModule):

  def defineResponses(self):
    self.respondToRegex('(image|img)( me| ma)? (.*)', imageMaResponse) 

#Response for the 'img ma' expression
def imageMaResponse(aMessage, **extraArgs):
  query = extraArgs['matchGroup'][2]
  result = imageMe(query)
  response = result if result else 'Nothing found for ' + query
  return aMessage.newResponseMessage(response)

#Searches google images for query and returns a random link
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
  