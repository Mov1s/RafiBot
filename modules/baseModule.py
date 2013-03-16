# -*- coding: utf8 -*- 
from ircBase import *
from random import randint
import MySQLdb as mdb
import ConfigParser
import os, sys, subprocess, time

config = ConfigParser.SafeConfigParser()
config.read('configs/ircBase.conf')

CONST_DB_USER = config.get('MySql', 'username')
CONST_DB_PASSWORD = config.get('MySql', 'password')

#Check if a message is requesting room history
#(in)aMessage - The message to check for the history query
#(out) The groups of the RegEx that matched
def getHistoryQuery(aMessage):
	expression = re.compile('(history|hist) (me|ma)(.*)', re.IGNORECASE)
	match = expression.match(aMessage.body)
	return match

#Create a new user in the database
#(in)aFirstName - The first name of the user to create
#(in)aLastName - The last name of the user to create
#(in)anEmail - The email address of the user to create
#(in)aMobileNumber - The mobile number of the user to create
#(out) The message to send to the irc room
def createUser(aFirstName, aLastName, anEmail, aMobileNumber):
	conn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot')
	cursor = conn.cursor()

	#Don't allow overlap of email address or phone number
	cursor.execute("SELECT id FROM Users u WHERE u.email = %s OR u.mobileNumber = %s", (anEmail, aMobileNumber))
	if cursor.rowcount != 0:
		return 'This mobile number or email is already in use'

	#Add the user
	creationTime = time.strftime('%Y-%m-%d %H:%M:%S')
	cursor.execute('INSERT INTO Users (firstName, lastName, email, mobileNumber, creationDate) VALUES (%s, %s, %s, %s, %s)', (aFirstName, aLastName, anEmail, aMobileNumber, creationTime))
	conn.commit()

	return aFirstName +  ' added!'

#Main module loop
def main(irc):
	message = irc.lastMessage()
	historyRequest = getHistoryQuery(message) if message.body != None else None

	#Quit when told to
	if message.botCommand == 'quit':
		ircMessage().newRoomMessage(irc, 'Later fags').send()
		ircMessage().newServerMessage(irc, 'QUIT').send()
		sys.exit()
	#Quit with update message
	elif message.botCommand == 'update':
		ircMessage().newRoomMessage(irc, 'Brb, updating').send()
		ircMessage().newServerMessage(irc, 'QUIT').send()

		#Call Rafi Git Update Script
		subprocess.call(["./rafiUpdater", "development"])

		#Restart Rafi
		os.execl(sys.executable, *([sys.executable]+sys.argv))
	#Print the last 10 room messages
	elif historyRequest:
		#Determine how many messages to show
		historyDepth = 10 if len(irc.messageLog) > 11 else len(irc.messageLog) - 1
		if historyRequest.group(3):
			try:
				historyDepth = int(historyRequest.group(3)) if int(historyRequest.group(3)) < len(irc.messageLog) else len(irc.messageLog) - 1
			except:
				return

		#Determine which messages the user wants to see
		historyCount = 0
		historyMessages = []
		for logMessage in reversed(irc.messageLog[:-1]):
			if logMessage.body != None:
				historyMessages.append(logMessage)
				historyCount += 1
			if historyCount >= historyDepth:
				break

		#PM the requested message history
		for historyMessage in reversed(historyMessages):
			sendingMessageBody = '{0}: {1}'.format(historyMessage.sendingNick, historyMessage.body)
			ircMessage().newPrivateMessage(irc, sendingMessageBody, message.sendingNick, offRecord = True).send()
	#Print Rafi's GitHub if someone mentions it
	elif message.containsKeywords(['git', irc.nick]):
		ircMessage().newRoomMessage(irc, 'My source is at https://github.com/Mov1s/RafiBot.git').send()
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
		ircMessage().newRoomMessage(irc, rafiQuotes[quoteIndex]).send()
	#Print 'Bewbs' if there has been no room activity for 30 min
	elif irc.noRoomActivityForTime(1800):
		ircMessage().newRoomMessage(irc, 'Bewbs').send()
	#Print the shiva blast if someone says shiva
	elif message.containsKeyword('shiva'):
		ircMessage().newRoomMessage(irc, 'SHIVAKAMINISOMAKANDAKRAAAAAAAM!').send()
	#Register a new user
	elif message.botCommand == 'adduser':
		response = ''
		if len(message.botCommandArguments) < 4:
			response = 'syntax is "adduser <FirstName> <LastName> <Email> <MobileNumber>"'
		else:
			args = message.botCommandArguments
			response = createUser(args[0], args[1], args[2], args[3])
	
		#Send out the response the same way it was recieved	
		if message.isPrivateMessage:
			ircMessage().newPrivateMessage(irc, response, message.sendingNick, offRecord = True).send()
		else:
			ircMessage().newRoomMessage(irc, response).send()
