from ircBase import *
import re
from random import randint
from datetime import date

#Define the images to link
fourdeezImages = []
fourdeezImages.append('https://www.dropbox.com/s/auf8gcy6q8n4y1e/Fourdeezz%20Bear.png')
fourdeezImages.append('https://www.dropbox.com/s/tpz37n67ece328t/Fourdeezz%20Hippo.png')

#Checks to see if a message contains 'tonight' but not 'tonight tonight'
def didFuckUpTonightTonight(message):
  ttExpression = re.compile('.*(tonight)( *)(tonight).*', re.IGNORECASE)
  tExpression = re.compile('.*(tonight).*', re.IGNORECASE)
  tonightTonightMatch = ttExpression.match(message)
  tonightMatch = tExpression.match(message)

  #Return true if they say 'tonight' and not 'tonight tonight'  
  if tonightMatch and not tonightTonightMatch:
    return True
  else:
    return False

def main(irc):
  message = irc.lastMessage()
  messages = []

  fourdeezMentioned = message.containsKeyword('four') or message.containsKeyword('40')
  weekday = date.today().weekday()

  #Only do things on Thursdays
  if(weekday == 3):
    #Randomly link fourdeez images
    if message.isPing:
      shouldShow = randint(0, 20) == 0
      if shouldShow:
        imageIndex = randint(0, len(fourdeezImages) - 1)
        messages.append(message.newRoomMessage('FOURDEEZ!! ' + fourdeezImages[imageIndex]))

    #Check some message bodys
    if message.body and fourdeezMentioned:
      messages.append(message.newResponseMessage('FOURDDEEEEZZZZ!!'))
    if message.body and didFuckUpTonightTonight(message.body):
      messages.append(message.newResponseMessage('tonight tonight*'))

    irc.sendMessages(messages)