from ircBase import *
from random import randint
import sys

#Because of importing ircBase a few variables are always available: nick, room, network, port
#So that is where those come from if you see them being used here

def main(irc):
	message = irc.lastMessage()

	#Quit when told to
	if messageIsBotCommand(message, 'quit'):
		irc.sendMessage('Later fags')
		irc.sendCommand('QUIT')
		sys.exit()
	#Quit with update message
	elif messageIsBotCommand(message, 'update'):
		irc.sendMessage('Brb, updating')
		irc.sendCommand('QUIT')
		sys.exit()
	#Print Rafi's GitHub if someone mentions it
	elif messageContainsKeywords(message, ['git', nick]):
		irc.sendMessage('My source is at https://github.com/Mov1s/RafiBot.git')
	#Print random Rafi quotes whenever rafi is mentioned
	elif messageContainsKeyword(message, nick):
		rafiQuotes = []
		rafiQuotes.append("I'm literally gonna sodomize you. I'm gonna have non consensual sex with your face and butt and then I'm going for your wife and children... Just kidding.")
		rafiQuotes.append("JUKEBOX! I'm gonna put $7 worth of Hoobastank in it!")
		rafiQuotes.append("*DICKPUNCH* Let's get the same girl pregnant tonight!")
		rafiQuotes.append("I don't know where you're gonna go! You might be finger blastin' somebody!")
		rafiQuotes.append("I think your face is gross, I think your boobs are different sizes, and I think *points to crotch* this is way too big!")
		rafiQuotes.append("I mean, you're such a good kisser, you got my dick hard, and I'm your brother.")
		rafiQuotes.append("Crotch-beer? Don't mind if I do!")
		rafiQuotes.append("We're also gonna sell your dick for gasoline.")
		rafiQuotes.append("Remember, his weak spot is his dick!")

		quoteIndex = randint(0, len(rafiQuotes) - 1)
		irc.sendMessage(rafiQuotes[quoteIndex])
	#Print 'Bewbs' if there has been no room activity for 30 min
	elif noRoomActivityForTime(irc, 1800):
		irc.sendMessage('Bewbs')