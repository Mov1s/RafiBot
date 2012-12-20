import socket
import time

network = 'irc.freenode.net'
port = 6667
room = '#MadsenRules'
nick = 'rafiTest'

#A class representing an IRC connection
#Keeps a reference to the IRC socket we are communicating on
#Keeps a reference of the last 20 messages sent over a chanel
class ircConnection():
	connection = None
	messageLog = []
	lastMessageWasPing = True
	lastMessageTimestamp = time.time()

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
		self.connection.send('PRIVMSG ' + room + ' :' + aMessage + '\r\n' )

	#Sends a PONG message message to the server when a PING is issued
	#(in)aPingMessage - The PING message that was issued from the server
	def sendPongForPing(self, aPingMessage):
		self.lastMessageWasPing = True
		self.connection.send ('PONG ' + aPingMessage.split()[1] + '\r\n')

	#Sends a command to the IRC server
	#(in)aCommand - The command to be sent to the server
	def sendCommand(self, aCommand):
		self.connection.send(aCommand + '\r\n')

#Creates an IRC connection using the constants at the top of the file
#(out) The newly created IRC connection
def createIrcConnection():
	irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	irc.connect((network, port))
	print irc.recv(4096)
	irc.send('NICK ' + nick + '\r\n')
	irc.send('USER ' + nick + ' ' + nick + ' ' + nick + ' :Python IRC\r\n')
	irc.send('JOIN ' + room + '\r\n')

	aConnection = ircConnection()
	aConnection.connection = irc
	return aConnection

#Checks to see if a message is a command meant for this bot
#(in) aMessage - The message that was recieved
#(in) aCommand - The command that you want to respond to
#(out) True or False depending on if you should respond to this command
def messageIsBotCommand(aMessage, aCommand):
	if aMessage == None: return False
	return aMessage.find('!' + nick + ' ' + aCommand) != -1

#Checks to see if a message in this room contains some keywords
#(in) aMessage - The message that was recieved
#(in) aKeyword - The keyword that you want to respond to
#(out) True or False depending on if you should respond to this keyword
def messageContainsKeyword(aMessage, aKeyword):
	if aMessage == None: return False
	isRoomMessage = aMessage.find('PRIVMSG ' + room) != -1
  	return isRoomMessage and aMessage.find(aKeyword) != -1

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