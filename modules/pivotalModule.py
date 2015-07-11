from ircBase import *
import urllib2
import json
import time
import ConfigParser

config = ConfigParser.SafeConfigParser()
config.read('configs/pivotalModule.conf')

API_TOKEN = config.get('PivotalModule', 'api_key')

time_of_last_check = int(time.time()) * 1000

@respondtoidletime(0)
def check_for_notifications(**exta_args):
  '''Check for recent notifications on a pivotal account'''
  notifications = get_pivotal_notifications_since_time(API_TOKEN, time_of_last_check)
  time_of_last_check = int(time.time()) * 1000

  #Construct the room alerts
  messages = []
  for notification in notifications:
    if notification['action'] == 'ownership':
      story_name = notification["story"]["name"]
      story_id = notification['story']['id']
      story_link = get_pivotal_url_for_story(story_id)

      message_body = 'New! [{0}] {1}'.format(story_id, story_name)
      messages.append(IrcMessage.new_room_message(message_body))
      messages.append(IrcMessage.new_room_message(story_link))

  return messages

def get_pivotal_notifications_since_time(api_key, time):
  '''Return an array of notifications for a pivotal account since a given epoch time'''
  pivotal_notification_uri = 'https://www.pivotaltracker.com/services/v5/my/notifications?created_after={0}'.format(time)
  headers = {'X-TrackerToken' : API_TOKEN}
  request = urllib2.Request(pivotal_notification_uri, headers = headers)
  response = urllib2.urlopen(request).read()
  return json.loads(response)

def get_pivotal_url_for_story(story_id):
  '''Return a url pointing to the story with the given story id'''
  pivotal_story_uri = 'https://www.pivotaltracker.com/services/v5/stories/{0}'.format(story_id)
  headers = {'X-TrackerToken' : API_TOKEN}
  request = urllib2.Request(pivotal_story_uri, headers = headers)
  response = urllib2.urlopen(request).read()
  story = json.loads(response)
  return story['url']


