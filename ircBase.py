import socket
import time
import re
import ConfigParser
import MySQLdb as mdb
from urlparse import urlparse

config = ConfigParser.SafeConfigParser()
config.read('configs/ircBase.conf')

CONST_NETWORK = config.get('Connection', 'server')
CONST_PORT = int(config.get('Connection', 'port'))
CONST_ROOM = config.get('Connection', 'room')
CONST_NICK = config.get('Connection', 'nick')
CONST_DB_USER = config.get('MySql', 'username')
CONST_DB_PASSWORD = config.get('MySql', 'password')

class IrcConnection():
    """A class representing an IRC connection.

    Keep a reference to the IRC socket we are communicating on.
    Keep a reference of the last 20 messages sent over a channel.

    """
    def __init__(self):
        """Intialize all the properties."""
        self.network = None
        self.port = None
        self.room = None
        self.nick = None

        self.connection = None
        self.messageLog = []
        self.lastMessageTimestamp = time.time()

    @staticmethod
    def newConnection(aNetwork = CONST_NETWORK, aPort = CONST_PORT, aRoom = CONST_ROOM, aNick = CONST_NICK):
        """Create and return an IRC connection using the constants at the top of the file."""
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

    def respondToServerMessages(self):
        """Main message handler for an IRC connection.

        Recieve messages from the server.
        Respond if it is a ping request.
        Otherwise log the message.

        """

        message = self.connection.recv(4096)

        #Check if the connection is still up
        if len(message) == 0:
          return None

        message = IrcMessage.newMessageFromRawMessage(message)
        if message.isPing:
            self.sendPongForPing(message)
        else:
						self.addMessageToLog(message)
        return message

    def addMessageToLog(self, aMessage):
        """Add a message to the message log."""
        self.messageLog.append(aMessage)
        if not aMessage.isPing:
            self.lastMessageTimestamp = time.time()
        if len(self.messageLog) > 40:
            del self.messageLog[0]

    def sendPongForPing(self, aPingMessage):
        """Send a PONG message message to the server when a PING is issued."""
        self.connection.send ('PONG ' + aPingMessage.rawMessage.split()[1] + '\r\n')

    def sendMessage(self, aMessage):
        """Send a message to the IRC server."""
        if aMessage.isRoomMessage:
            fullMessage = aMessage.recievingRoom + ' :' + aMessage.body + '\r\n'
            self.connection.send('PRIVMSG ' + fullMessage)
        elif aMessage.isPrivateMessage:
            fullMessage = aMessage.privateMessageRecipient + ' :' + aMessage.body + '\r\n'
            self.connection.send('PRIVMSG ' + fullMessage)
        elif aMessage.isServerMessage:
            self.connection.send(aMessage.body + '\r\n')

        if not aMessage.isOffRecord: self.addMessageToLog(aMessage)

    def sendMessages(self, someMessages):
        """Send a list of messages to the IRC server."""
        for message in someMessages:
            self.sendMessage(message)

    def noRoomActivityForTime(self, timeInSeconds):
        """Return True if there has been any activity in a given period of time."""
        currentTime = time.time()
        return currentTime - self.lastMessageTimestamp >= timeInSeconds


class IrcMessage():
    """Class representing an IRC message.

    Contain static methods for constructing new messages.
    Contain usefull properties for identifying messages.

    """
    def __init__(self):
        """Initialize all the properties."""
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

    @staticmethod
    def newMessageFromRawMessage(aRawMessage):
        """Create and return a new IrcMessage object from a raw irc message string."""
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

    @staticmethod
    def newRoomMessage(theMessageBody, aRoom = None, offRecord = False):
        """Create and return a new IrcMessage object to be sent out to a room."""
        if aRoom == None: aRoom = CONST_ROOM
        spoofRawMessage = ':{0}! PRIVMSG {1} :{2}\r\n'.format(CONST_NICK, aRoom, theMessageBody)
        spoofMessage = IrcMessage.newMessageFromRawMessage(spoofRawMessage)
        spoofMessage.isOffRecord = offRecord
        return spoofMessage

    @staticmethod
    def newPrivateMessage(theMessageBody, aRecievingNick, offRecord = True):
        """Create and return a new IrcMessage object to be sent out to a nick."""
        spoofRawMessage = ':{0}! PRIVMSG {1} :{2}\r\n'
        spoofRawMessage = spoofRawMessage.format(CONST_NICK, aRecievingNick, theMessageBody)
        spoofMessage = IrcMessage.newMessageFromRawMessage(spoofRawMessage)
        spoofMessage.isOffRecord = offRecord
        return spoofMessage

    @staticmethod
    def newServerMessage(theMessageBody, offRecord = True):
        """Create and return a new IrcMessage object to be sent out to the server."""
        spoofMessage = IrcMessage()
        spoofMessage.body = theMessageBody
        spoofMessage.isServerMessage = True
        spoofMessage.isOffRecord = offRecord
        return spoofMessage 
    
    def newResponseMessage(self, theMessageBody):
        """Create and return a new IrcMessage object that is a direct response to this message.

        If this message is a PM then the response will be a PM back to that person.
        If this message is anything else the response is a room message.

        """
        newMessage = None
        if self.isPrivateMessage:
            newMessage = IrcMessage.newPrivateMessage(theMessageBody, self.sendingNick)
        else:
            newMessage = IrcMessage.newRoomMessage(theMessageBody, self.recievingRoom)
        return newMessage
    

class IrcModule:
    """Class representing an IRC module.

    Keep a list of filters and actions to evaluate against messages.

    """
    def __init__(self):
        self.ircBot = None
        self.regexActions = {}
        self.idleActions = {}
        self.botCommandActions = {}
        self.defineResponses()

    def do(self, someMessage):
        """Evaluate a message against all of the filters and return a list of messages."""
        regexResponses = self.evaluateRegexes(someMessage)
        idleResponses = self.evaluateIdleTimes()
        botCommandResponses = self.evaluateBotCommands(someMessage)
        return regexResponses + idleResponses + botCommandResponses

    def defineResponses():
        """Define the filters this module responds too.  Override in subclasses."""
        return

    def evaluateRegexes(self, someMessage):
        """Check all of the Regex filters and return a list of messages."""
        #Return imediatley if the message does not have a body
        if not someMessage.body:
            return []

        #Test the message against each regex filter in this module
        responses = []
        for regex, action in self.regexActions.iteritems():
            matchGroup = self.evaluateMessageAgainstRegex(regex, someMessage.body)
            if matchGroup != None:
                messages = action(someMessage, matchGroup=matchGroup)
                if isinstance(messages, list):
                   responses = responses + messages
                elif messages:
                    responses.append(messages)
        return responses

    def evaluateIdleTimes(self):
        """Check all of the idle time filters and return a list of messages."""
        responses = []
        for idleTime, action in self.idleActions.iteritems():
            if(self.ircBot.irc.noRoomActivityForTime(idleTime)):
                messages = action(ircConnection=self.ircBot.irc)
                if isinstance(messages, list):
                   responses = responses + messages
                elif messages:
                    responses.append(messages)
        return responses

    def evaluateBotCommands(self, someMessage):
        """Check all of the bot command filters and return a list of messages."""
        #Return imediatley if the message is not a bot command
        if not someMessage.isBotCommand:
            return []

        #Test the message against each bot command filter in this module
        responses = []
        for botCommand, action in self.botCommandActions.iteritems():
            if botCommand == someMessage.botCommand:
                messages = action(someMessage)
                if isinstance(messages, list):
                    responses = responses + messages
                elif messages:
                    responses.append(messages)
        return responses

    def evaluateMessageAgainstRegex(self, aRegex, aMessageBody):
        """Perform a regex on a message body and return an array of match parts."""
        expression = re.compile(aRegex, re.IGNORECASE)
        match = expression.match(aMessageBody)
        return match.groups() if match else None

    def respondToRegex(self, aKeyword, anAction):
        """Register a regex to respond to and the action to perform."""
        self.regexActions[aKeyword] = anAction

    def respondToIdleTime(self, timeInSeconds, anAction):
        """Register an idle time to respond to and the action to perform."""
        self.idleActions[timeInSeconds] = anAction

    def respondToBotCommand(self, aBotCommand, anAction):
        """Register a bot command to respond to and the action to perform."""
        self.botCommandActions[aBotCommand] = anAction


class IrcBot(object):
    """Class representing an IRC bot.

    Keep a connection to the server and respond to IRC actiity.
    Keep a list of modules to be run against IRC activity.

    """
    def __init__(self):
        """Initialize the bot with the default IRC connection."""
        self._databaseConnection = None
        self.irc = IrcConnection.newConnection()
        self.modules = []

    def attachModule(self, aModule):
        """Add a movule to the list of modules this bot should evaluate."""
        aModule.ircBot = self
        self.modules.append(aModule)

    def databaseConnection(self):
        """Construct a database connection if there is not one and return it."""
        if not self._databaseConnection:
            self._databaseConnection = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD)
        return self._databaseConnection

    def run(self):
        """Start the bot responding to IRC activity."""
        while True:
            server_message = self.irc.respondToServerMessages()

            #Reconnect if needed
            if not server_message:
                self.irc = IrcConnection.newConnection()
                continue

            messages = []
            for module in self.modules:
                messages = messages + module.do(server_message)
            self.irc.sendMessages(messages)

            print server_message.rawMessage
