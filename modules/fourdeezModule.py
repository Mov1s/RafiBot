from ircBase import *
from random import randint
from datetime import date
import re

#Define the images to link
fourdeez_images = []
fourdeez_images.append('https://www.dropbox.com/s/zxzd30en1g6w0gk/Fourdeeezzzz%20Ape.png')
fourdeez_images.append('https://www.dropbox.com/s/8yvynoqzgflm053/Fourdeeezzzz%20Busey.png')
fourdeez_images.append('https://www.dropbox.com/s/a9vbs9x9935z71q/Fourdeeezzzz%20Cagerous.png')
fourdeez_images.append('https://www.dropbox.com/s/aped6xf3w0d3q2i/Fourdeeezzzz%20Horses.png')
fourdeez_images.append('https://www.dropbox.com/s/3swjsjenkfazso7/Fourdeeezzzz%20Loude%20Noises.png')
fourdeez_images.append('https://www.dropbox.com/s/bo6inwweldfz6j3/Fourdeeezzzz%20Rambo.png')
fourdeez_images.append('https://www.dropbox.com/s/49f0uuvchrp44cj/Fourdeeezzzz%20Woods.png')
fourdeez_images.append('https://www.dropbox.com/s/7xcqzfkgyc3qghn/Fourdeezz%20Bear.png')
fourdeez_images.append('https://www.dropbox.com/s/haq780vh93xv97i/Fourdeezz%20Hippo.png')
fourdeez_images.append('http://i.imgur.com/CA8U1m1.gif')
fourdeez_images.append('http://i.imgur.com/FQ3IR0m.gif')

class FourdeezModule(IrcModule):

  def defineResponses(self):
    self.respondToRegex('.*(four|40).*', self.fourdeez_response)
    self.respondToIdleTime(600, self.fourdeez_images_response)
    self.respondToRegex('.*(tonight).*', self.correct_tonight_response)

  def fourdeez_response(self, aMessage, **extraArgs):
    if today_is_thursday():
      return aMessage.newResponseMessage("FOURDEEEEZZZZ!!")

  def fourdeez_images_response(self, **extraArgs):
    previousMessage = self.ircBot.irc.messageLog[-1]

    if today_is_thursday() and previousMessage.sendingNick != self.ircBot.irc.nick:
      image_index = randint(0, len(fourdeez_images) - 1)
      return IrcMessage.newRoomMessage('FOURDEEZ!! ' + fourdeez_images[image_index])

  def correct_tonight_response(self, aMessage, **extraArgs):
    if today_is_thursday():
      tt_expression = re.compile('.*(tonight)( *)(tonight).*', re.IGNORECASE)
      tonight_tonight_match = tt_expression.match(aMessage.body)

      #Return true if they say 'tonight' and not 'tonight tonight'
      if not tonight_tonight_match:
        return aMessage.newResponseMessage('tonight tonight*')

def today_is_thursday():
  weekday = date.today().weekday()
  return True if weekday == 3 else False


