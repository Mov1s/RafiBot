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
class IrcConnection():

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

        aConnection = IrcConnection()
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
        message = IrcMessage.newMessageFromRawMessage(message)
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

    #Sends an array of messages to the IRC server
    #(in)someMessages - The array of messages to be sent
    def sendMessages(self, someMessages):
        for message in someMessages:
            self.sendMessage(message)

    #Checks to see if there has been any activity in a given period of time
    #(in)timeInSeconds - The time frame to monitor for activity
    #(out) True or False depending on if there has been any activity in the given time frame
    def noRoomActivityForTime(self, timeInSeconds):
        currentTime = time.time()
        return currentTime - self.lastMessageTimestamp >= timeInSeconds

class IrcMessage():
    #Initializes all the properties
    def __init__(self):
        #Message properties
        self.rawMessage = None
        self.body = None
        self.botCommand = None
        self.sendingNick = None
        self.recievingRoom = None
        self.privateMessageRecipient = None
        self.links = []
        self.botCommandArguments = []

        #Usefull flags
        self.hasLinks = False
        self.isPrivateMessage = False
        self.isServerMessage = False
        self.isRoomMessage = False
        self.isPing = False
        self.isBotCommand = False
        self.isOffRecord = False

    #Creates a new IrcMessage object from a raw irc message string
    #(in)aRawMessage - The message string as it comes from the server
    #(out) A shiny new IrcMessage object
    @staticmethod
    def newMessageFromRawMessage(aRawMessage):
        newMessage = IrcMessage()
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
            bcExpression = re.compile(':!' + CONST_NICK + ' (.*)', re.IGNORECASE)
            match = bcExpression.search(newMessage.rawMessage)
            if match:
                newMessage.botCommand = match.group(1).split()[0].strip()
                newMessage.botCommandArguments = match.group(1).split()[1:]
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

    #Creates a new IrcMessage object to be sent out to a room
    #(in)theMessageBody - The body text for the new irc message
    #(in)aRoom - [optional] The room to send the message to if it is different than the default room of the irc connection
    #(in)offRecord - [optional] A flag for whether or not to keep this message in the message log
    #(out) A new IrcMessage object
    @staticmethod
    def newRoomMessage(theMessageBody, aRoom = None, offRecord = False):
        if aRoom == None: aRoom = CONST_ROOM
        spoofRawMessage = ':{0}! PRIVMSG {1} :{2}\r\n'.format(CONST_NICK, aRoom, theMessageBody)
        spoofMessage = IrcMessage.newMessageFromRawMessage(spoofRawMessage)
        spoofMessage.isOffRecord = offRecord
        return spoofMessage

    #Creates a new IrcMessage object to be sent out to a nick
    #(in)theMessageBody - The body text for the new irc message
    #(in)aRecievingNick - The nick to send the message to
    #(in)offRecord - [optional] A flag for whether or not to keep this message in the message log
    #(out) A new IrcMessage object
    @staticmethod
    def newPrivateMessage(theMessageBody, aRecievingNick, offRecord = True):
        spoofRawMessage = ':{0}! PRIVMSG {1} :{2}\r\n'.format(CONST_NICK, aRecievingNick, theMessageBody)
        spoofMessage = IrcMessage.newMessageFromRawMessage(spoofRawMessage)
        spoofMessage.isOffRecord = offRecord
        return spoofMessage

    #Creates a new IrcMessage object to be sent out to the server
    #(in)theMessageBody - The body text for the new irc message
    #(in)offRecord - [optional] A flag for whether or not to keep this message in the message log
    #(out) A new IrcMessage object
    @staticmethod
    def newServerMessage(theMessageBody, offRecord = True):
        spoofMessage = IrcMessage()
        spoofMessage.body = theMessageBody
        spoofMessage.isServerMessage = True
        spoofMessage.isOffRecord = offRecord
        return spoofMessage 

    #Creates a new IrcMessage object that is meant to be a direct response to this message
    #If this message is a PM then the response will be a PM back to that person, if this message is anything else the response is a room message
    #(in) theMessageBody - The body text for the new irc message
    #(out) A new IrcMessage object
    def newResponseMessage(self, theMessageBody):
        newMessage = None
        if self.isPrivateMessage:
            newMessage = IrcMessage.newPrivateMessage(theMessageBody, self.sendingNick)
        else:
            newMessage = IrcMessage.newRoomMessage(theMessageBody, self.recievingRoom)
        return newMessage

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

#A class representing an IRC module
class IrcModule:

    def __init__(self):
        self.ircBot = None
        self.regexActions = {}
        self.idleActions = {}
        self.defineResponses()

    #Checks all actions of this module against a message
    def do(self, someMessage):
        regexResponses = self.evaluateRegexes(someMessage)
        idleResponses = self.evaluateIdleTimes()
        return regexResponses + idleResponses

    #Override for subclasses to define what to respond too
    def defineResponses():
        return

    #Check all of the Regex filters and return their messages
    def evaluateRegexes(self, someMessage):
        if not someMessage.body:
            return []

        responses = []
        for regex, action in self.regexActions.iteritems():
            matchGroup = self.evaluateRegex(regex, someMessage.body)
            if matchGroup:
                messages = action(someMessage, matchGroup=matchGroup, ircConnection=self.ircBot.irc)
                if isinstance(messages, list):
                   responses = responses + messages
                elif messages:
                    responses.append(messages)
        return responses

    #Check all of the idle time filters and return their messages
    def evaluateIdleTimes(self):
        responses = []
        for idleTime, action in self.idleActions.iteritems():
            if(self.ircBot.irc.noRoomActivityForTime(idleTime)):
                messages = action(ircConnection=self.ircBot.irc)
                if isinstance(messages, list):
                   responses = responses + messages
                elif messages:
                    responses.append(messages)
        return responses

    #Return an array of match parts for a regex and string
    def evaluateRegex(self, aRegex, aMessageBody):
        expression = re.compile(aRegex, re.IGNORECASE)
        match = expression.match(aMessageBody)
        return match.groups() if match else None

    #Register a regex to respond to
    def respondToRegex(self, aKeyword, anAction):
        self.regexActions[aKeyword] = anAction

    #Register an idle time to respond to
    def respondToIdleTime(self, timeInSeconds, anAction):
        self.idleActions[timeInSeconds] = anAction

class IrcBot:

    def __init__(self):
        self.irc = IrcConnection.newConnection()
        self.modules = []

    def attachModule(self, aModule):
        aModule.ircBot = self
        self.modules.append(aModule)

    def run(self):
        while True:
            self.irc.respondToServerMessages()

            messages = []
            for module in self.modules:
                messages = messages + module.do(self.irc.lastMessage())
            self.irc.sendMessages(messages)

            print self.irc.lastMessage().rawMessage
