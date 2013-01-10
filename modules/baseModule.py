# -*- coding: utf8 -*- 
from ircBase import *
from random import randint
import sys

def main(irc):
	message = irc.lastMessage()

	#Quit when told to
	if message.botCommand == 'quit':
		irc.sendMessageToRoom('Later fags')
		irc.sendCommand('QUIT')
		sys.exit()
	#Quit with update message
	elif message.botCommand == 'update':
		irc.sendMessageToRoom('Brb, updating')
		irc.sendCommand('QUIT')
		sys.exit()
	#Print Rafi's GitHub if someone mentions it
	elif message.containsKeywords(['git', irc.nick]):
		irc.sendMessageToRoom('My source is at https://github.com/Mov1s/RafiBot.git')
	#Print random Rafi quotes whenever rafi is mentioned
	elif message.containsKeyword(irc.nick) and not message.isBotCommand:
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
		rafiQuotes.append("I roofied like 40% of the drinks here. It's a numbers game.")
		rafiQuotes.append("Spoiler Alert! Guess what the landlord is gonna find when he unclogs the toilet?? Haha... His fucking cat!")
		rafiQuotes.append("I could watch her walk out of a room for hours. My sister’s body is bonkers. I hope you are hitting that!!")
		rafiQuotes.append("I'm day drunk, get ready to see my dick.")
		rafiQuotes.append("Sometimes when I puke I shit.")

		quoteIndex = randint(0, len(rafiQuotes) - 1)
		irc.sendMessageToRoom(rafiQuotes[quoteIndex])
	#Print 'Bewbs' if there has been no room activity for 30 min
	elif noRoomActivityForTime(irc, 1800):
		irc.sendMessageToRoom('Bewbs')
