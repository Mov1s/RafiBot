import socket
import time
import re

initNetwork = 'irc.freenode.net'
initPort = 6667
initRoom = '#MadsenTest'
initNick = 'rafiMadsen'

#A class representing an IRC connection
#Keeps a reference to the IRC socket we are communicating on
#Keeps a reference of the last 20 messages sent over a chanel
class ircConnection():
	connection = None
	messageLog = []
	lastMessageWasPing = True
	lastMessageTimestamp = time.time()
	network = initNetwork
	port = initPort 
	room = initRoom
	nick = initNick

	#Adds a message to the message log
	#(in)aMessage - The message to add to message log
	def addMessageToLog(self, aMessage):
		self.lastMessageWasPing = False
		self.messageLog.append(aMessage)
		self.lastMessageTimestamp = time.time()
		if len(self.messageLog) > 20:
			del self.messageLog[0]

	#Returns the last recieved message
	#(out) The last message in the connection log
	def lastMessage(self):
		return self.messageLog[-1] if self.lastMessageWasPing == False else None

	#Sends a message to the IRC room
	#(in)aMessage - The message to be sent to the room
	def sendMessage(self, aMessage):
		self.addMessageToLog(aMessage)
		self.connection.send('PRIVMSG ' + self.room + ' :' + aMessage + '\r\n' )

	#Sends a PONG message message to the server when a PING is issued
	#(in)aPingMessage - The PING message that was issued from the server
	def sendPongForPing(self, aPingMessage):
		self.lastMessageWasPing = True
		self.connection.send ('PONG ' + aPingMessage.split()[1] + '\r\n')

	#Sends a command to the IRC server
	#(in)aCommand - The command to be sent to the server
	#TODO - Find a way around using initNick
	def sendCommand(self, aCommand):
		global initNick
			
		self.connection.send(aCommand + '\r\n')
		if(aCommand.lower().find('join') <> -1):
			self.connection.send('part ' + self.room + '\r\n')
			self.room = aCommand[aCommand.lower().rfind('join') + 5:].rstrip()
		elif(aCommand.lower().find('nick') <> -1):
			self.nick = aCommand[aCommand.lower().rfind('nick') + 5:].rstrip().lstrip()
			initNick = self.nick

#Creates an IRC connection using the constants at the top of the file
#(out) The newly created IRC connection
def createIrcConnection():
	irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	irc.connect((initNetwork, initPort))
	print irc.recv(4096)
	irc.send('NICK ' + initNick + '\r\n')
	irc.send('USER ' + initNick + ' ' + initNick + ' ' + initNick + ' :Python IRC\r\n')
	irc.send('JOIN ' + initRoom + '\r\n')

	aConnection = ircConnection()
	aConnection.connection = irc
	return aConnection

#Checks to see if a message is a command meant for this bot
#(in) aMessage - The message that was recieved
#(in) aCommand - The command that you want to respond to
#(out) True or False depending on if you should respond to this command
#TODO - Find a way to not use initNick
def messageIsBotCommand(aMessage, aCommand):
	if aMessage == None: return False
	return aMessage.find('!' + initNick + ' ' + aCommand) != -1

#Checks to see if a message in this room contains a single keyword
#(in) aMessage - The message that was recieved
#(in) aKeyword - The keyword that you want to respond to
#(out) True or False depending on if you should respond to this keyword
def messageContainsKeyword(aMessage, aKeyword):
	return messageContainsKeywords(aMessage, [aKeyword])

#Checks to see if a message in this room contains some keywords
#(in) aMessage - The message that was recieved
#(in) someKeywords - A list of keywords that you want to respond to
#(out) True or False depending on if you should respond to these keywords
def messageContainsKeywords(aMessage, someKeywords):
	if aMessage == None: return False
	isRoomMessage = messageIsForRoom(aMessage)

	keywordsArePresent = True
	for keyword in someKeywords:
		if aMessage.find(keyword) == -1: keywordsArePresent = False

  	return isRoomMessage and keywordsArePresent

#Checks to see if the message is a private message for the room
#(in) aMessage - The message that was recieved
#(out) True or False depending on if the message was private to the room
def messageIsForRoom(aMessage):
	if aMessage == None: return False
	expression = re.compile('PRIVMSG #(.*) :(.*)', re.IGNORECASE)
  	match = expression.search(aMessage)
	isRoomMessage = True if match else False
	return isRoomMessage

#Returns the body of a message (the text that a person says, striped of all server text)
#(in) aMessage - The message that was recieved
#(out) String of just the message's body
def bodyOfMessage(aMessage):
	if aMessage == None: return None
	expression = re.compile('PRIVMSG (.*) :(.*)', re.IGNORECASE)
  	match = expression.search(aMessage)
	if match:
			return match.group(2)
	return None

#Checks to see if the message is from a given nick
#(in) aMessage - The message that was recieved
#(in) aNick - The nick you want to see if the message was from
#(out) True or False depending on if the message was from the given nick
def messageIsFromNick(aMessage, aNick):
	if aMessage == None: return False
	nick = aMessage[1:aMessage.find('!')]
	return True if aNick == nick else False

#Checks to see if there has been any activity in a given period of time
#(in)aConnection - The IRC connection to monitor for activity
#(in)timeInSeconds - The time frame to monitor for activity
#(out) True or False depending on if there has been any activity in the given time frame
def noRoomActivityForTime(aConnection, timeInSeconds):
	currentTime = time.time()
	return currentTime - aConnection.lastMessageTimestamp >= timeInSeconds

#Main message handler for an IRC bot
#Recieves message from the server, responds if it is a ping request, otherwise log the message
#(in)aConnection - IRC connection to monitor
#(out) The updated IRC connection
def respondToServerMessages(aConnection):
	message = aConnection.connection.recv(4096)
	if message.find('PING') != -1:
	 	aConnection.sendPongForPing(message)
	else:
		aConnection.addMessageToLog(message)
	return aConnection
