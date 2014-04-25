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

CONST_DB_USER = config.get('MySql', 'username')
CONST_DB_PASSWORD = config.get('MySql', 'password')

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
            bcExpression = re.compile(':!(.*)', re.IGNORECASE)
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
    def newRoomMessage(theMessageBody, offRecord = False):
        """Create and return a new IrcMessage object to be sent out to a room."""
        spoofMessage = IrcMessage()
        spoofMessage.isRoomMessage = True
        spoofMessage.body = theMessageBody
        spoofMessage.isOffRecord = offRecord
        return spoofMessage

    @staticmethod
    def newPrivateMessage(theMessageBody, aRecievingNick, offRecord = True):
        """Create and return a new IrcMessage object to be sent out to a nick."""
        spoofMessage = IrcMessage()
        spoofMessage.isPrivateMessage = True
        spoofMessage.privateMessageRecipient = aRecievingNick
        spoofMessage.body = theMessageBody
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
            newMessage = IrcMessage.newRoomMessage(theMessageBody)
        return newMessage


class IrcBot(object):
    """Singleton class representing an IRC bot.

    Keep a connection to the server and respond to IRC actiity.

    """
    _instance = None

    def __init__(self):
        """Initialize the bot with the default IRC connection."""
        self._database_connection = None
        self.response_evaluator = ResponseEvaluator()

        self.nick = None
        self.room = None
        self._server = None
        self._server_port = None

        self.connection = None
        self.messageLog = []
        self.lastMessageTimestamp = time.time()

    @classmethod
    def shared_instance(cls):
        '''Singleton instance retriever.  Creates a new instance if there is not already one.'''
        if IrcBot._instance == None:
            IrcBot._instance = IrcBot()
        return IrcBot._instance

    def connect(self, attempt = 0, max_attempts = 10):
        '''Attempt connecting to the IRC server
        Retry up to max_attempts before giving up and failing'''

        print "Attempting connection {0}...".format(attempt)

        #Configure the settings if they are not already set up
        if not self.is_configured(): self.configure_from_file()

        #Attempt connection to the irc server
        connection_was_successfull = False 
        try:
            newConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            newConnection.connect((self._server, self._server_port))
            print newConnection.recv(4096)

            newConnection.send('NICK ' + self.nick + '\r\n')
            newConnection.send('USER ' + self.nick + ' ' + self.nick + ' ' + self.nick + ' :Python IRC\r\n')
            newConnection.send('JOIN ' + self.room + '\r\n')
            self.connection = newConnection
            connection_was_successfull = True 
        except Exception, e:
            connection_was_successfull = False 

        #If connection failed recurse and try again
        if not connection_was_successfull and attempt < 10:
            connection_was_successfull = self.connect(attempt + 1, max_attempts)
        return connection_was_successfull

    def _wait_for_message_from_server(self, attempt = 0, max_attempts = 10):
        """Main message handler for an IRC connection.

        Recieve messages from the server.
        Respond if it is a ping request.
        Otherwise log the message.

        """

        message = self.connection.recv(4096) if self.connection else None

        #Check if the connection is still up
        if message == None or len(message) == 0:
            if not self.connect() or attempt >= max_attempts:
                return None
            else:
                return self._wait_for_message_from_server(attempt + 1)

        #Respond to ping or add to log
        message = IrcMessage.newMessageFromRawMessage(message)
        if message.isPing:
            self._send_pong_for_ping(message)
        elif not message.isServerMessage and message.isRoomMessage:
            self._add_message_to_log(message)
        return message

    def _send_pong_for_ping(self, aPingMessage):
        """Send a PONG message message to the server when a PING is issued."""
        self.connection.send ('PONG ' + aPingMessage.rawMessage.split()[1] + '\r\n')

    def _add_message_to_log(self, aMessage):
        """Add a message to the message log."""

        self.messageLog.append(aMessage)
        if not aMessage.isPing:
            self.lastMessageTimestamp = time.time()
        if len(self.messageLog) > 40:
            del self.messageLog[0]

    def sendMessage(self, aMessage):
        """Send a message to the IRC server."""
        if aMessage.isRoomMessage:
            fullMessage = self.room + ' :' + aMessage.body + '\r\n'
            self.connection.send('PRIVMSG ' + fullMessage)
        elif aMessage.isPrivateMessage:
            fullMessage = aMessage.privateMessageRecipient + ' :' + aMessage.body + '\r\n'
            self.connection.send('PRIVMSG ' + fullMessage)
        elif aMessage.isServerMessage:
            self.connection.send(aMessage.body + '\r\n')

        aMessage.sendingNick = self.nick
        if not aMessage.isOffRecord: self._add_message_to_log(aMessage)

    def sendMessages(self, someMessages):
        """Send a list of messages to the IRC server."""
        for message in someMessages:
            self.sendMessage(message)

    def is_configured(self):
        '''Checks if the values needed to connect to an irc server are set'''
        return self.nick and self.room and self._server and self._server_port

    def noRoomActivityForTime(self, timeInSeconds):
        """Return True if there has been any activity in a given period of time."""
        currentTime = time.time()
        return currentTime - self.lastMessageTimestamp >= timeInSeconds

    def configure_from_file(self, a_config_file = 'configs/ircBase.conf'):
        '''Configure the connection params of this bot from a config file'''
        config = ConfigParser.SafeConfigParser()
        config.read(a_config_file)

        self._server = config.get('Connection', 'server')
        self._server_port = int(config.get('Connection', 'port'))
        self.room = config.get('Connection', 'room')
        self.nick = config.get('Connection', 'nick')

    def database_connection(self):
        """Construct a database connection if there is not one and return it."""
        if not self._database_connection:
            self._database_connection = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD)
        return self._database_connection

    def run(self):
        """Start the bot responding to IRC activity."""

        #Start the main loop
        while True:

            server_message = self._wait_for_message_from_server()

            #No server message means unable to connect to server
            if not server_message:
                print "Failed to connect to the server..."
                break

            #Perform the module actions
            messages = self.response_evaluator.evaluate_responses_for_message(server_message)
            self.sendMessages(messages)

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
        if(IrcBot.shared_instance().noRoomActivityForTime(idle_time)):
            messages = action()
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