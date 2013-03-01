import socket
import time
import re
import ConfigParser
from urlparse import urlparse

config = ConfigParser.SafeConfigParser()
config.read('configs/ircBase.conf')

CONST_NETWORK = config.get('Connection', 'server')
CONST_PORT = int(config.get('Connection', 'port'))
CONST_ROOM = config.get('Connection', 'room')
CONST_NICK = config.get('Connection', 'nick')

#A class representing an IRC connection
#Keeps a reference to the IRC socket we are communicating on
#Keeps a reference of the last 20 messages sent over a chanel
class ircConnection():

	#Intializes all the properties
	def __init__(self):
		self.network = None
		self.port = None
		self.room = None
		self.nick = None

		self.connection = None
		self.messageLog = []
		self.lastMessageTimestamp = time.time()

	#Creates an IRC connection using the constants at the top of the file
	#(out) The newly created IRC connection
	@staticmethod
	def newConnection(aNetwork = CONST_NETWORK, aPort = CONST_PORT, aRoom = CONST_ROOM, aNick = CONST_NICK):
		newConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		newConnection.connect((aNetwork, aPort))
		print newConnection.recv(4096)
		newConnection.send('NICK ' + aNick + '\r\n')
		newConnection.send('USER ' + aNick + ' ' + aNick + ' ' + aNick + ' :Python IRC\r\n')
		newConnection.send('JOIN ' + aRoom + '\r\n')

		aConnection = ircConnection()
		aConnection.connection = newConnection
		aConnection.network = aNetwork
		aConnection.port = aPort
		aConnection.room = aRoom
		aConnection.nick = aNick
		return aConnection

	#Main message handler for an IRC bot
	#Recieves message from the server, responds if it is a ping request, otherwise log the message
	def respondToServerMessages(self):
		message = self.connection.recv(4096)
		message = ircMessage().newMessageFromRawMessage(self, message)
		if message.isPing:
			self.sendPongForPing(message)
		self.addMessageToLog(message)

	#Adds a message to the message log
	#(in)aMessage - The message to add to message log
	def addMessageToLog(self, aMessage):
		self.messageLog.append(aMessage)
		if not aMessage.isPing:
			self.lastMessageTimestamp = time.time()
		if len(self.messageLog) > 20:
			del self.messageLog[0]

	#Returns the last recieved message
	#(out) The last message in the connection log
	def lastMessage(self):
		return self.messageLog[-1]

	#Sends a PONG message message to the server when a PING is issued
	#(in)aPingMessage - The PING message that was issued from the server
	def sendPongForPing(self, aPingMessage):
		self.connection.send ('PONG ' + aPingMessage.rawMessage.split()[1] + '\r\n')

	#Sends a message to the IRC server
	#(in)aMessage - The message to be sent
	def sendMessage(self, aMessage):
		if aMessage.isRoomMessage:
			self.connection.send('PRIVMSG ' + aMessage.recievingRoom + ' :' + aMessage.body + '\r\n')
		elif aMessage.isPrivateMessage:
			self.connection.send('PRIVMSG ' + aMessage.privateMessageRecipient + ' :' + aMessage.body + '\r\n')
		elif aMessage.isServerMessage:
			self.connection.send(aMessage.body + '\r\n')

		if not aMessage.isOffRecord: self.addMessageToLog(aMessage)

	#Checks to see if there has been any activity in a given period of time
	#(in)timeInSeconds - The time frame to monitor for activity
	#(out) True or False depending on if there has been any activity in the given time frame
	def noRoomActivityForTime(self, timeInSeconds):
		currentTime = time.time()
		return currentTime - self.lastMessageTimestamp >= timeInSeconds

class ircMessage():
	#Initializes all the properties
	def __init__(self):
		self.ircConnection = None

		#Message properties
		self.rawMessage = None
		self.body = None
		self.botCommand = None
		self.sendingNick = None
		self.recievingRoom = None
		self.privateMessageRecipient = None
		self.links = []

		#Usefull flags
		self.hasLinks = False
		self.isPrivateMessage = False
		self.isServerMessage = False
		self.isRoomMessage = False
		self.isPing = False
		self.isBotCommand = False
		self.isOffRecord = False

	#Creates a new ircMessage object from a raw irc message string
	#(in)anIrcConnection - The IRC connection that this message was recieved on
	#(in)aRawMessage - The message string as it comes from the server
	#(out) A shiny new ircMessage object
	@staticmethod
	def newMessageFromRawMessage(anIrcConnection, aRawMessage):
		newMessage = ircMessage()
		newMessage.ircConnection = anIrcConnection
		newMessage.rawMessage = aRawMessage

		#Get sending nick
		nickExpression = re.compile(':(.*)!', re.IGNORECASE)
	  	match = nickExpression.search(newMessage.rawMessage[:18])
		if match:
			newMessage.sendingNick = match.group(1).strip()
		else:
			newMessage.isServerMessage = True

		#Get private message or room message
		if not newMessage.isServerMessage:
			roomExpression = re.compile('PRIVMSG (#.*) :(.*)', re.IGNORECASE)
  			match = roomExpression.search(newMessage.rawMessage)
  			if match:
	  			newMessage.body = match.group(2).strip()
	  			newMessage.recievingRoom = match.group(1).strip()
	  			newMessage.isRoomMessage = True
	  		else:
	  			pmExpression = re.compile('PRIVMSG (.*) :(.*)', re.IGNORECASE)
  				match = pmExpression.search(newMessage.rawMessage)
  				if match:
  					newMessage.body = match.group(2).strip()
  					newMessage.privateMessageRecipient = match.group(1).strip()
  					newMessage.isPrivateMessage = True

  		#Get bot command
  		if not newMessage.isServerMessage:
  			bcExpression = re.compile(':!' + anIrcConnection.nick + ' (.*)', re.IGNORECASE)
  			match = bcExpression.search(newMessage.rawMessage)
  			if match:
  				newMessage.botCommand = match.group(1).split()[0].strip()
  				newMessage.isBotCommand = True

  		#Get ping
  		if newMessage.isServerMessage:
  			pingExpression = re.compile('PING (.*)', re.IGNORECASE)
  			match = pingExpression.search(newMessage.rawMessage)
  			if match:
  				newMessage.isPing = True

  		#Get links
  		if not newMessage.body == None:
  			wordArray = newMessage.body.split()
  			for word in wordArray:
  				url = urlparse(word)
				if url.scheme == 'http' or url.scheme == 'https':
					newMessage.hasLinks = True
					newMessage.links.append(word)

  		return newMessage

  	#Creates a new ircMessage object to be sent out to a room
  	#(in)anIrcConnection - The IRC connection that this message should be sent on
  	#(in)theMessageBody - The body text for the new irc message
  	#(in)aRoom - [optional] The room to send the message to if it is different than the default room of the irc connection
  	#(in)offRecord - [optional] A flag for whether or not to keep this message in the message log
  	#(out) A new ircMessage object
  	@staticmethod
  	def newRoomMessage(anIrcConnection, theMessageBody, aRoom = None, offRecord = False):
		if aRoom == None: aRoom = anIrcConnection.room
		spoofRawMessage = ':{0}! PRIVMSG {1} :{2}\r\n'.format(anIrcConnection.nick, aRoom, theMessageBody)
		spoofMessage = ircMessage().newMessageFromRawMessage(anIrcConnection, spoofRawMessage)
		spoofMessage.isOffRecord = offRecord
		return spoofMessage

	#Creates a new ircMessage object to be sent out to a nick
  	#(in)anIrcConnection - The IRC connection that this message should be sent on
  	#(in)theMessageBody - The body text for the new irc message
  	#(in)aRecievingNick - The nick to send the message to
  	#(in)offRecord - [optional] A flag for whether or not to keep this message in the message log
  	#(out) A new ircMessage object
	@staticmethod
  	def newPrivateMessage(anIrcConnection, theMessageBody, aRecievingNick, offRecord = True):
		spoofRawMessage = ':{0}! PRIVMSG {1} :{2}\r\n'.format(anIrcConnection.nick, aRecievingNick, theMessageBody)
		spoofMessage = ircMessage().newMessageFromRawMessage(anIrcConnection, spoofRawMessage)
		spoofMessage.isOffRecord = offRecord
		return spoofMessage

	#Creates a new ircMessage object to be sent out to the server
  	#(in)anIrcConnection - The IRC connection that this message should be sent on
  	#(in)theMessageBody - The body text for the new irc message
  	#(in)offRecord - [optional] A flag for whether or not to keep this message in the message log
  	#(out) A new ircMessage object
	@staticmethod
	def newServerMessage(anIrcConnection, theMessageBody, offRecord = True):
		spoofMessage = ircMessage()
		spoofMessage.ircConnection = anIrcConnection
		spoofMessage.body = theMessageBody
		spoofMessage.isServerMessage = True
		spoofMessage.isOffRecord = offRecord
		return spoofMessage	

	#Sends the message out on the message's irc connection
	def send(self):
		self.ircConnection.sendMessage(self)

	#Checks to see if a message in this room contains a single keyword
	#(in) aKeyword - The keyword that you want to respond to
	#(out) True or False depending on if you should respond to this keyword
	def containsKeyword(self, aKeyword):
		return self.containsKeywords([aKeyword])

	#Checks to see if a message in this room contains some keywords
	#(in) someKeywords - A list of keywords that you want to respond to
	#(out) True or False depending on if you should respond to these keywords
	def containsKeywords(self, someKeywords):
		if self.body == None: return False

		keywordsArePresent = True
		for keyword in someKeywords:
			if self.body.find(keyword) == -1: keywordsArePresent = False

	  	return keywordsArePresent
