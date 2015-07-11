from ircBase import *
import urllib2
import json
from random import randint

GOOGLE_API_URL = 'http://ajax.googleapis.com'
URI_FORMAT = '/ajax/services/search/images?v=1.0&rsz=8&q='

@respondtoregex('(image|img)( me| ma)? (.*)')
def img_ma_response(message, **extra_args):
  '''Response for the 'img ma' expression'''
  query = extra_args['match_group'][2]
  image_link = random_image_link_for_query(query)
  response = image_link if image_link else 'Nothing found for ' + query
  return message.new_response_message(response)

#Searches google images for query and returns a random link
def random_image_link_for_query(query):
  try:
    query = query.replace(' ', '+')
    url = GOOGLE_API_URL + URI_FORMAT + query
    response = urllib2.urlopen(url)
    response_string = response.read()
    response_JSON = json.loads(response_string)
    length = len(response_JSON['responseData']['results'])
    if length > 0:
      image = response_JSON['responseData']['results'][randint(0, length - 1)]['unescapedUrl']
      return image
  except:
    return None
  
