from ircBase import *
import re
from random import randint
from datetime import date

#Define the images to link
fourdeezImages = []
fourdeezImages.append('https://www.dropbox.com/s/zxzd30en1g6w0gk/Fourdeeezzzz%20Ape.png')
fourdeezImages.append('https://www.dropbox.com/s/8yvynoqzgflm053/Fourdeeezzzz%20Busey.png')
fourdeezImages.append('https://www.dropbox.com/s/a9vbs9x9935z71q/Fourdeeezzzz%20Cagerous.png')
fourdeezImages.append('https://www.dropbox.com/s/aped6xf3w0d3q2i/Fourdeeezzzz%20Horses.png')
fourdeezImages.append('https://www.dropbox.com/s/3swjsjenkfazso7/Fourdeeezzzz%20Loude%20Noises.png')
fourdeezImages.append('https://www.dropbox.com/s/bo6inwweldfz6j3/Fourdeeezzzz%20Rambo.png')
fourdeezImages.append('https://www.dropbox.com/s/49f0uuvchrp44cj/Fourdeeezzzz%20Woods.png')
fourdeezImages.append('https://www.dropbox.com/s/7xcqzfkgyc3qghn/Fourdeezz%20Bear.png')
fourdeezImages.append('https://www.dropbox.com/s/haq780vh93xv97i/Fourdeezz%20Hippo.png')
fourdeezImages.append('http://i.imgur.com/CA8U1m1.gif')

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
