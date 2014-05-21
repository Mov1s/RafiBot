# -*- coding: utf8 -*- 
from ircBase import *
from random import randint
import MySQLdb as mdb
import ConfigParser
import os, sys, subprocess, time, datetime

config = ConfigParser.SafeConfigParser()
config.read('configs/ircBase.conf')

CONST_DB_USER = config.get('MySql', 'username')
CONST_DB_PASSWORD = config.get('MySql', 'password')
  
@respondtobotcommand('quit')  
def quit_response(message, **extra_args):
  """Respond to a command to quit."""
  later_msg = IrcMessage.new_room_message('Later fags')
  quit_msg = IrcMessage.new_server_message('QUIT')
  IrcBot.shared_instance().send_messages([later_msg, quit_msg])
  sys.exit()

@respondtobotcommand('update')
def update_response(message, **extra_args):
  """Respond to a command to update."""
  update_msg = IrcMessage.new_room_message('Brb, updating')
  quit_msg = IrcMessage.new_server_message('QUIT')
  IrcBot.shared_instance().send_messages([update_msg, quit_msg])

  #Call Rafi Git Update Script
  subprocess.call(["./rafiUpdater", "master"])

  #Restart Rafi
  os.execl(sys.executable, *([sys.executable]+sys.argv))

@respondtoregex('(history|hist) (me|ma)(.*)')
def hist_ma_response(message, **extra_args):
  """Respond to a 'hist ma' request."""
  #Determine how many messages to show
  message_log = IrcBot.shared_instance().message_log
  history_depth = 10 if len(message_log) > 11 else len(message_log) - 1

  #Determine which messages the user wants to see
  history_count = 0
  history_messages = []
  for log_message in reversed(message_log[:-1]):
    if log_message.body != None:
      history_messages.append(log_message)
      history_count += 1
    if history_count >= history_depth:
      break

  #PM the requested message history
  return_messages = []
  for historyMessage in reversed(history_messages):
    sendingMessageBody = '{0}: {1}'.format(historyMessage.sending_nick, historyMessage.body)
    return_messages.append(IrcMessage.new_private_message(sendingMessageBody, message.sending_nick))
  return return_messages

@respondtoregex('.*')
def runtime_evaluation_response(message, **extra_args):
  """Evaluates for every message.

    Used to evaluate a regex at runtime instead of when the module
    is instantiated.  I check for the bot name in the regex which
    isn't available during instantiation.

  """
  #Return if it is a bot command
  if message.is_bot_command:
    return

  #Regex for mentioning the bot name
  quote_regex = '.*{0}.*'.format(IrcBot.shared_instance().nick)
  quote_expression = re.compile(quote_regex, re.IGNORECASE)
  didMentionBot = quote_expression.match(message.body) != None

  #Regex for people talking about bot git
  git_regex = '(.*git.*{0}.*)|(.*{0}.*git.*)'.format(IrcBot.shared_instance().nick)
  git_expression = re.compile(git_regex, re.IGNORECASE)
  didMentionGit = git_expression.match(message.body) != None

  #Return message for one or the other
  if didMentionGit:
    return message.new_response_message('My source is at https://github.com/Mov1s/RafiBot.git')
  elif didMentionBot:
    return message.new_response_message(random_rafi_quote())


@respondtoidletime(1800)
def bewbs_response(**extra_args):
  """Respond with 'Bewbs'."""
  previousMessage = IrcBot.shared_instance().message_log[-1]
  if not message_is_bewbs(previousMessage):
    return IrcMessage.new_room_message('Bewbs')

@respondtoregex('.*(shiva).*')
def shiva_response(message, **extra_args):
  """Respond with shiva blast."""
  return IrcMessage.new_room_message('SHIVAKAMINISOMAKANDAKRAAAAAAAM!')

@respondtobotcommand('adduser')
def add_user_response(message, **extra_args):
  """Register a new user."""
  response = ''
  if len(message.bot_command_arguments) < 4:
    response = 'syntax is "adduser <FirstName> <LastName> <Email> <MobileNumber>"'
  else:
    args = message.bot_command_arguments
    response = createUser(args[0], args[1], args[2], args[3])

  return message.new_response_message(response)

@respondtobotcommand('addnick')
def add_nick_response(message, **extra_args):
  """Add a new alias or nick for a user."""
  response = ''
  if len(message.bot_command_arguments) < 2:
    response = 'syntax is "addnick <Email> <Nick>"'
  else:
    args = message.bot_command_arguments
    response = addNickForEmail(args[0], args[1])

  return message.new_response_message(response)

@respondtobotcommand('userinfo')
def user_info_response(message, **extra_args):
  """Return user details for a search string."""
  response = ''
  if len(message.bot_command_arguments) < 1:
    response = 'syntax is "userinfo <SearchString>"'
  else:
    args = message.bot_command_arguments
    response = informationForUser(args[0])

  return message.new_response_message(response)


def createUser(aFirstName, aLastName, anEmail, aMobileNumber):
  """Create a new user in the database."""
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
  cursor.close()

  return aFirstName +  ' added!'

def addNickForEmail(anEmail, aNick):
  """Create a new nick or alias for a user."""
  conn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot')
  cursor = conn.cursor()

  #Don't allow overlap of nicks
  cursor.execute("SELECT id FROM Nicks n WHERE n.nick = %s", (aNick))
  if cursor.rowcount != 0:
    return 'This nick is already in use'
  
  #Get the user to link the nick to
  userId = userFirstName  = ''
  cursor.execute("SELECT id, firstName FROM Users u WHERE u.email = %s", (anEmail))
  if cursor.rowcount == 0:
    return 'There is no user with this email address'
  else:
    result = cursor.fetchall()
    userId = result[0][0]
    userFirstName = result[0][1]

  #Add the nick
  creationTime = time.strftime('%Y-%m-%d %H:%M:%S')
  cursor.execute('INSERT INTO Nicks (nick, userId, creationDate) VALUES (%s, %s, %s)', (aNick, userId, creationTime))
  conn.commit()
  cursor.close()

  return aNick +  ' linked to ' + userFirstName + "!"

def informationForUser(theSearchString):
  """List the contact info for a nick or name."""
  conn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot')
  cursor = conn.cursor()

  #Get the user
  cursor.execute("SELECT n.nick, u.firstName, u.lastName, u.email, u.mobileNumber, unix_timestamp(u.creationDate)  FROM Nicks n LEFT JOIN Users u ON u.id = n.userId WHERE n.nick = %s or u.firstName = %s or u.lastName = %s", (theSearchString, theSearchString, theSearchString))
  if cursor.rowcount == 0:
    cursor.close()
    return 'No user was found for this string'
  else:
    result = cursor.fetchall()
    now = time.time()
    userNick = result[0][0]
    userFirstName = result[0][1]
    userLastName = result[0][2]
    userEmail = result[0][3]
    userNumber = result[0][4]
    userSince = now - result[0][5]
    cursor.close()
    return userFirstName + " " + userLastName + ", user for " + str(datetime.timedelta(seconds = int(userSince))) + ", " + userEmail + " " + userNumber

def random_rafi_quote():
    """Generate a random Rafi quote."""
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
    return rafiQuotes[quoteIndex]

def message_is_bewbs(aMessage):
  return aMessage.body.find('Bewbs') != -1
