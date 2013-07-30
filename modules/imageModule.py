from ircBase import *
import urllib2
import json
import re
from random import randint

googleAPI = 'http://ajax.googleapis.com'
uriFormat = '/ajax/services/search/images?v=1.0&rsz=8&q='

class ImageModule(IrcModule):

  def defineResponses(self):
    self.respondToRegex('(image|img)( me| ma)? (.*)', img_ma_response) 

#Response for the 'img ma' expression
def img_ma_response(message, **extra_args):
  query = extra_args['matchGroup'][2]
  image_link = random_image_link_for_query(query)
  response = image_link if result else 'Nothing found for ' + query
  return message.newResponseMessage(response)

#Searches google images for query and returns a random link
def random_image_link_for_query(query):
  try:
    query = query.replace(' ', '+')
    url = googleAPI + uriFormat + query
    response = urllib2.urlopen(url)
    responseString = response.read()
    responseJSON = json.loads(responseString)
    length = len(responseJSON['responseData']['image_links'])
    if length > 0:
      image = responseJSON['responseData']['image_links'][randint(0, length - 1)]['unescapedUrl']
      return image
  except:
    return None
  
