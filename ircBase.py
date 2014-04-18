import logging
import socket
import time
import re
import ConfigParser
import MySQLdb as mdb
from urlparse import urlparse

logging.basicConfig(filename='modules.log', level=logging.ERROR)

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
        elif not message.isServerMessage and message.isRoomMessage:
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


class IrcBot(object):
    """Singleton class representing an IRC bot.

    Keep a connection to the server and respond to IRC actiity.

    """
    _instance = None

    def __init__(self):
        """Initialize the bot with the default IRC connection."""
        self._database_connection = None
        self.irc = IrcConnection.newConnection()
        self.response_evaluator = ResponseEvaluator()

    @classmethod
    def shared_instance(cls):
        '''Singleton instance retriever.  Creates a new instance if there is not already one.'''
        if IrcBot._instance == None:
            IrcBot._instance = IrcBot()
        return IrcBot._instance

    def database_connection(self):
        """Construct a database connection if there is not one and return it."""
        if not self._database_connection:
            self._database_connection = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD)
        return self._database_connection

    def run(self):
        """Start the bot responding to IRC activity."""

        #Start the main loop
        while True:
            server_message = self.irc.respondToServerMessages()

            #Reconnect if needed
            if not server_message:
                self.irc = IrcConnection.newConnection()
                continue

            #Perform the module actions
            messages = self.response_evaluator.evaluate_responses_for_message(server_message)
            self.irc.sendMessages(messages)

            #Close the database connection
            if self._database_connection:
              self._database_connection.close()
            self._database_connection = None

            print server_message.rawMessage


class ResponseEvaluator:
    """Class for keeping track of responses and evaluating them

    Responses can be registered with the evaluator and when requested it will evaluate all of the responses
    against an IrcMessage and return a list of response messages.

    """

    def __init__(self, some_responses = []):
        '''Initialize the evaluator with some responses'''
        self._responses = some_responses

    def register_response(self, a_response):
        '''Adds a response to the list of responses to be evaluated against a message'''
        self._responses.append(a_response)

    def evaluate_responses_for_message(self, a_message):
        '''Evaluates all registered responses against an IrcMessage, returns a list of messages'''
        messages = []
        for response in self._responses:
            if response.type == Response.REGEX_RESPONSE:
                messages = messages + self.evaluate_regex_response(response, a_message)
            elif response.type == Response.COMMAND_RESPONSE:
                messages = messages + self.evaluate_bot_command(response, a_message)
            elif response.type == Response.IDLE_RESPONSE:
                messages = messages + self.evaluate_idle_time(response)
        return messages

    def evaluate_regex_response(self, a_response, a_message):
        '''Check a regex filter and return a list of messages.'''
        #Return imediatley if the message does not have a body
        if not a_message.body:
            return []

        #Setup
        responses = []
        regex = a_response.condition
        action = a_response.action

        #Test the message against the regex filter
        expression = re.compile(regex, re.IGNORECASE)
        match = expression.match(a_message.body)
        match_group =  match.groups() if match else None

        #Return response messages if the regex matched
        if match_group != None:
            messages = action(a_message, matchGroup = match_group)
            if isinstance(messages, list):
                responses = responses + messages
            elif messages:
                responses.append(messages)
        return responses

    def evaluate_bot_command(self, a_response, a_message):
        '''Check a bot command filter and return a list of messages.'''
        #Return imediatley if the message is not a bot command
        if not a_message.isBotCommand:
            return []

        #Setup
        responses = []
        bot_command = a_response.condition
        action = a_response.action

        #Return response messages if the bot command matched
        if bot_command == a_message.botCommand:
            messages = action(a_message)
            if isinstance(messages, list):
                responses = responses + messages
            elif messages:
                responses.append(messages)
        return responses

    def evaluate_idle_time(self, a_response):
        '''Check an idle time filter and return a list of messages.'''

        #Setup
        responses = []
        idle_time = a_response.condition
        action = a_response.action

        #Return response messages if the idle time has been passed
        if(IrcBot.shared_instance().irc.noRoomActivityForTime(idle_time)):
            messages = action(ircConnection = IrcBot.shared_instance().irc)
            if isinstance(messages, list):
               responses = responses + messages
            elif messages:
                responses.append(messages)
        return responses


class Response:
    """Class representing a response filter"""

    REGEX_RESPONSE = 'regex'
    COMMAND_RESPONSE = 'botcommand'
    IDLE_RESPONSE = 'idletime'

    def __init__(self, a_type, a_condition, an_action):
        self.type = a_type
        self.condition = a_condition
        self.action = an_action

def respondtoregex(regex):
    '''Registers a regex filter response with the shared IrcBot'''
    def wrapper(func):
        response = Response(Response.REGEX_RESPONSE, regex, func)
        IrcBot.shared_instance().response_evaluator.register_response(response)
        return func
    return wrapper

def respondtobotcommand(command):
    '''Registers a bot command filter response with the shared IrcBot'''
    def wrapper(func):
        response = Response(Response.COMMAND_RESPONSE, command, func)
        IrcBot.shared_instance().response_evaluator.register_response(response)
        return func
    return wrapper

def respondtoidletime(idle_time):
    '''Registers an idle time response with the shared IrcBot'''
    def wrapper(func):
        response = Response(Response.IDLE_RESPONSE, idle_time, func)
        IrcBot.shared_instance().response_evaluator.register_response(response)
        return func
    return wrapper