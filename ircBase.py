import logging
import inspect
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
        self.raw_message = None
        self.body = None
        self.bot_command = None
        self.sending_nick = None
        self.recieving_room = None
        self.private_message_recipient = None
        self.links = []
        self.bot_command_arguments = []

        #Usefull flags
        self.has_links = False
        self.is_private_message = False
        self.is_server_message = False
        self.is_room_message = False
        self.is_ping = False
        self.is_bot_command = False
        self.is_off_record = False

    @staticmethod
    def new_message_from_raw_message(a_raw_message):
        """Create and return a new IrcMessage object from a raw irc message string."""
        new_message = IrcMessage()
        new_message.raw_message = a_raw_message

        #Get sending nick
        nick_expression = re.compile(':(.*)!', re.IGNORECASE)
        match = nick_expression.search(new_message.raw_message[:18])
        if match:
            new_message.sending_nick = match.group(1).strip()
        else:
            new_message.is_server_message = True

        #Get private message or room message
        if not new_message.is_server_message:
            room_expression = re.compile('PRIVMSG (#.*) :(.*)', re.IGNORECASE)
            match = room_expression.search(new_message.raw_message)
            if match:
                new_message.body = match.group(2).strip()
                new_message.recieving_room = match.group(1).strip()
                new_message.is_room_message = True
            else:
                pm_expression = re.compile('PRIVMSG (.*) :(.*)', re.IGNORECASE)
                match = pm_expression.search(new_message.raw_message)
                if match:
                    new_message.body = match.group(2).strip()
                    new_message.private_message_recipient = match.group(1).strip()
                    new_message.is_private_message = True

        #Get bot command
        if not new_message.is_server_message and new_message.body != None:
            bc_expression = re.compile('^!(.*)', re.IGNORECASE)
            match = bc_expression.search(new_message.body)
            if match:
                new_message.bot_command = match.group(1).split()[0].strip()
                new_message.bot_command_arguments = match.group(1).split()[1:]
                new_message.is_bot_command = True

        #Get ping
        if new_message.is_server_message:
            ping_expression = re.compile('PING (.*)', re.IGNORECASE)
            match = ping_expression.search(new_message.raw_message)
            if match:
                new_message.is_ping = True

        #Get links
        if not new_message.body == None:
            word_array = new_message.body.split()
            for word in word_array:
                url = urlparse(word)
                if url.scheme == 'http' or url.scheme == 'https':
                    new_message.has_links = True
                    new_message.links.append(word)

        return new_message

    @staticmethod
    def new_room_message(the_message_body, off_record = False):
        """Create and return a new IrcMessage object to be sent out to a room."""
        spoof_message = IrcMessage()
        spoof_message.is_room_message = True
        spoof_message.body = the_message_body
        spoof_message.is_off_record = off_record
        return spoof_message

    @staticmethod
    def new_private_message(the_message_body, a_recieving_nick, off_record = True):
        """Create and return a new IrcMessage object to be sent out to a nick."""
        spoof_message = IrcMessage()
        spoof_message.is_private_message = True
        spoof_message.private_message_recipient = a_recieving_nick
        spoof_message.body = the_message_body
        spoof_message.is_off_record = off_record
        return spoof_message

    @staticmethod
    def new_server_message(the_message_body, off_record = True):
        """Create and return a new IrcMessage object to be sent out to the server."""
        spoof_message = IrcMessage()
        spoof_message.body = the_message_body
        spoof_message.is_server_message = True
        spoof_message.is_off_record = off_record
        return spoof_message

    def new_response_message(self, the_message_body):
        """Create and return a new IrcMessage object that is a direct response to this message.

        If this message is a PM then the response will be a PM back to that person.
        If this message is anything else the response is a room message.

        """
        new_message = None
        if self.is_private_message:
            new_message = IrcMessage.new_private_message(the_message_body, self.sending_nick)
        else:
            new_message = IrcMessage.new_room_message(the_message_body)
        return new_message


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
        self._timeout = 240

        self.connection = None
        self.message_log = []
        self.last_message_timestamp = time.time()

    @classmethod
    def shared_instance(cls):
        '''Singleton instance retriever.  Creates a new instance if there is not already one.'''
        if IrcBot._instance == None:
            IrcBot._instance = IrcBot()
        return IrcBot._instance

    @classmethod
    def formatted_module_exception_title(cls):
        '''Grabs the last exception and formats an exception title from the module it occurred in.'''
        frame = inspect.trace()[-1]
        module = inspect.getmodule(frame[0])
        module_name = module.__name__ if module else "Unknown Module"
        return "Module Error: " + module_name

    def connect(self, attempt = 0, max_attempts = 10):
        '''Attempt connecting to the IRC server
        Retry up to max_attempts before giving up and failing'''

        print "Attempting connection {0}...".format(attempt)

        #Configure the settings if they are not already set up
        if not self.is_configured(): self.configure_from_file()

        #Attempt connection to the irc server
        connection_was_successful = False
        try:
            newConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            newConnection.settimeout(self._timeout)
            newConnection.connect((self._server, self._server_port))
            print newConnection.recv(4096)

            newConnection.send('NICK ' + self.nick + '\r\n')
            newConnection.send('USER ' + self.nick + ' ' + self.nick + ' ' + self.nick + ' :Python IRC\r\n')
            newConnection.send('JOIN ' + self.room + '\r\n')
            self.connection = newConnection
            connection_was_successful = True
        except Exception, e:
            connection_was_successful = False

        #If connection failed recurse and try again
        if not connection_was_successful and attempt < 10:
            connection_was_successful = self.connect(attempt + 1, max_attempts)
        return connection_was_successful

    def _wait_for_message_from_server(self):
        """Main message handler for an IRC connection.

        Recieve messages from the server.
        Respond if it is a ping request.
        Otherwise log the message.

        """

        message = self.connection.recv(4096) if self.connection else None

        #Check if the connection is still up
        if message == None or len(message) == 0:
            raise socket.error("connection lost")

        #Respond to ping or add to log
        message = IrcMessage.new_message_from_raw_message(message)
        if message.is_ping:
            self._send_pong_for_ping(message)
        elif not message.is_server_message and message.is_room_message:
            self._add_message_to_log(message)
        return message

    def _send_pong_for_ping(self, a_ping_message):
        """Send a PONG message message to the server when a PING is issued."""
        self.connection.send ('PONG ' + a_ping_message.raw_message.split()[1] + '\r\n')

    def _add_message_to_log(self, a_message):
        """Add a message to the message log."""

        self.message_log.append(a_message)
        if not a_message.is_ping:
            self.last_message_timestamp = time.time()
        if len(self.message_log) > 40:
            del self.message_log[0]

    def send_message(self, a_message):
        """Send a message to the IRC server."""
        if a_message.is_room_message:
            full_message = self.room + ' :' + a_message.body + '\r\n'
            self.connection.send('PRIVMSG ' + full_message)
        elif a_message.is_private_message:
            full_message = a_message.private_message_recipient + ' :' + a_message.body + '\r\n'
            self.connection.send('PRIVMSG ' + full_message)
        elif a_message.is_server_message:
            self.connection.send(a_message.body + '\r\n')

        a_message.sending_nick = self.nick
        if not a_message.is_off_record: self._add_message_to_log(a_message)

    def send_messages(self, some_messages):
        """Send a list of messages to the IRC server."""
        for message in some_messages:
            self.send_message(message)

    def is_configured(self):
        '''Checks if the values needed to connect to an irc server are set'''
        return self.nick and self.room and self._server and self._server_port

    def no_room_activity_for_time(self, time_in_seconds):
        """Return True if there has been any activity in a given period of time."""
        current_time = time.time()
        return current_time - self.last_message_timestamp >= time_in_seconds

    def configure_from_file(self, a_config_file = 'configs/ircBase.conf'):
        '''Configure the connection params of this bot from a config file'''
        config = ConfigParser.SafeConfigParser()
        config.read(a_config_file)

        self._server = config.get('Connection', 'server')
        self._server_port = int(config.get('Connection', 'port'))
        self._timeout = int(config.get('Connection', 'timeout'))
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

            #Connect if the connection is closed
            if not self.connection and not self.connect(): break

            #Listen for IRC activity and perform the module actions
            try:
                server_message = self._wait_for_message_from_server()
                print server_message.raw_message

                messages = self.response_evaluator.evaluate_responses_for_message(server_message)
                self.send_messages(messages)

            #Catch errors when the connection gets reset
            except (socket.error, socket.timeout):
                self.connection = None
                logging.exception("Server connection lost")

            #Catch errors generated by modules
            except Exception:
                exception_title = IrcBot.formatted_module_exception_title()
                logging.exception(exception_title)
                self.send_message(IrcMessage.new_room_message(exception_title))

            #Close the database connection
            if self._database_connection:
              self._database_connection.close()
            self._database_connection = None


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
        response_messages = []
        for response in self._responses:
            if response.type == Response.REGEX_RESPONSE:
                response_messages = response_messages + self.evaluate_regex_response(response, a_message)
            elif response.type == Response.COMMAND_RESPONSE:
                response_messages = response_messages + self.evaluate_bot_command(response, a_message)
            elif response.type == Response.IDLE_RESPONSE:
                response_messages = response_messages + self.evaluate_idle_time(response)
        return response_messages

    def evaluate_regex_response(self, a_response, a_message):
        '''Check a regex filter and return a list of messages.'''
        #Return imediatley if the message does not have a body
        if not a_message.body:
            return []

        #Setup
        response_messages = []
        regex = a_response.condition
        action = a_response.action

        #Test the message against the regex filter
        expression = re.compile(regex, re.IGNORECASE)
        match = expression.match(a_message.body)
        match_group =  match.groups() if match else None

        #Return response messages if the regex matched
        if match_group != None:
            messages = action(a_message, match_group = match_group)
            if isinstance(messages, list):
                response_messages = messages
            elif messages:
                response_messages = [messages]
        return response_messages

    def evaluate_bot_command(self, a_response, a_message):
        '''Check a bot command filter and return a list of messages.'''
        #Return imediatley if the message is not a bot command
        if not a_message.is_bot_command:
            return []

        #Setup
        response_messages = []
        bot_command = a_response.condition
        action = a_response.action

        #Return response messages if the bot command matched
        if bot_command == a_message.bot_command:
            messages = action(a_message)
            if isinstance(messages, list):
                response_messages = messages
            elif messages:
                response_messages = [messages]
        return response_messages

    def evaluate_idle_time(self, a_response):
        '''Check an idle time filter and return a list of messages.'''

        #Setup
        response_messages = []
        idle_time = a_response.condition
        action = a_response.action

        #Return response messages if the idle time has been passed
        if(IrcBot.shared_instance().no_room_activity_for_time(idle_time)):
            messages = action()
            if isinstance(messages, list):
               response_messages = messages
            elif messages:
                response_messages = [messages]
        return response_messages


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
