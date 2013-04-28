from ircBase import *
import MySQLdb as mdb
import time
import datetime
import ConfigParser

config = ConfigParser.SafeConfigParser()
config.read('configs/ircBase.conf')

CONST_DB_USER = config.get('MySql', 'username')
CONST_DB_PASSWORD = config.get('MySql', 'password')

#------------------------------------------------------------------
#Module Query Methods
#------------------------------------------------------------------

#Check if message is a request to start tracking AP
#(in)aMessageBody - The body of the message to check for patern
#(out) True or False depending on if the message matches the patern
def apStartQuery(aMessageBody):
	expression = re.compile('(track ap start)', re.IGNORECASE)
	match = expression.match(aMessageBody)
	return True if match else False

#Check if message is a request to stop tracking AP
#(in)aMessageBody - The body of the message to check for patern
#(out) True or False depending on if the message matches the patern
def apStopQuery(aMessageBody):
	expression = re.compile('(track ap stop)', re.IGNORECASE)
	match = expression.match(aMessageBody)
	return True if match else False

#Check if message is a request to print stats of AP
#(in)aMessageBody - The body of the message to check for patern
#(out) True or False depending on if the message matches the patern
def apStatsQuery(aMessageBody):
	expression = re.compile('(track ap stats)', re.IGNORECASE)
	match = expression.match(aMessageBody)
	return True if match else False

#------------------------------------------------------------------
#MySQL AP Methods
#------------------------------------------------------------------

#Start tracking the time of an AP
#(in)aMessageNick - The nick to start tracking for
#(out) The message to print to the room
def startTrackingApForNick(aMessageNick):
	apConn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'moduleApTracker')
	userConn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot')
	apCursor = apConn.cursor()
	userCursor = userConn.cursor()

	#Get the UserId for this nick
	userCursor.execute("SELECT userId FROM Nicks WHERE nick = %s", (aMessageNick))
	if userCursor.rowcount == 0:
		return 'This nick is not linked to a registered user'
	userId = userCursor.fetchall()[0][0]

	#Don't allow the user to start another AP if they still have one open
	apCursor.execute("SELECT id FROM ApRecord ar WHERE ar.userId = %s and ar.endTime IS NULL", (userId))
	if apCursor.rowcount != 0:
		return 'You are already drinking an AP'

	#Start a new AP record
	startTime = time.strftime('%Y-%m-%d %H:%M:%S')
	apCursor.execute("INSERT INTO ApRecord (userId, startTime) VALUES (%s, %s)", (userId, startTime))
	apConn.commit()

	return 'Bottoms up!'

#Stop tracking the current AP
#(in)aMessageNick - The nick to stop tracking for
#(out) The message to print to the room
def stopTrackingApForNick(aMessageNick):
	apConn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'moduleApTracker')
	userConn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot')
	apCursor = apConn.cursor()
	userCursor = userConn.cursor()

	#Get the UserId for this nick
	userCursor.execute("SELECT userId FROM Nicks WHERE nick = %s", (aMessageNick))
	if userCursor.rowcount == 0:
		return 'This nick is not linked to a registered user'
	userId = userCursor.fetchall()[0][0]

	#Don't allow the user to stop AP if they don't have one started
	apCursor.execute("SELECT id, unix_timestamp(startTime) FROM ApRecord ar WHERE ar.userId = %s and ar.endTime IS NULL", (userId))
	if apCursor.rowcount != 0:
		result = apCursor.fetchall()
		startTime = result[0][1]

		#Calculate the AP duration
		endTime = time.strftime('%Y-%m-%d %H:%M:%S')
		endTimeInt = time.time()
		duration = endTimeInt - startTime

		#Close AP record
		recordId = result[0][0]
		apCursor.execute("UPDATE ApRecord SET endTime = %s, duration = %s WHERE id = %s", (endTime, duration, recordId))
		apConn.commit()

		return 'That AP took you ' + str(datetime.timedelta(seconds = duration))
	else:
		return 'You haven\'t started drinking an AP'

#Get a user's AP stats
#(in)aMessageNick - The nick to report stats for
#(out) The message to print to the room
def getApStatsForNick(aMessageNick):
	apConn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'moduleApTracker')
	userConn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot')
	apCursor = apConn.cursor()
	userCursor = userConn.cursor()

	#Get the UserId for this nick
	userCursor.execute("SELECT userId FROM Nicks WHERE nick = %s", (aMessageNick))
	if userCursor.rowcount == 0:
		return 'This nick is not linked to a registered user'
	userId = userCursor.fetchall()[0][0]

	statMessage = ''
	#Get the total time of all complete APs and the count of how many have been drank
	apCursor.execute("SELECT COUNT(id), SUM(duration) FROM ApRecord ar WHERE ar.userId = %s and ar.endTime IS NOT NULL", (userId))
	result = apCursor.fetchall()
	totalAps = result[0][0]
	if totalAps != 0:
		totalDuration = result[0][1]
		formatedDuration = str(datetime.timedelta(seconds = int(totalDuration)))

		statMessage = 'You have drank ' + str(totalAps) + ' AP(s) for a total time of ' + formatedDuration + '.  '

	#Check to see if there are any open APs and report stats on those
	apCursor.execute("SELECT unix_timestamp(startTime) FROM ApRecord ar WHERE ar.userId = %s and ar.endTime IS NULL", (userId))
	if apCursor.rowcount != 0:
		result = apCursor.fetchall()
		startTime = result[0][0]
		duration = time.time() - startTime

		statMessage += 'You have been drinking your current AP for ' + str(datetime.timedelta(seconds = duration)) + '.'
	
	#If there are no stats report that
	if statMessage == '':
		statMessage = 'Nothing to report'

	return statMessage

def main(irc):
	message = irc.lastMessage()
	messages = []

	#Needs message body
	if message.body == None:
		return

	#Start tracking an AP
	if apStartQuery(message.body):
		returnMessage = startTrackingApForNick(message.sendingNick)
		messages.append(ircMessage().newRoomMessage(returnMessage))
	#Stop tracking an AP
	elif apStopQuery(message.body):
		returnMessage = stopTrackingApForNick(message.sendingNick)
		messages.append(ircMessage().newRoomMessage(returnMessage))
	#Print the stats for AP
	elif apStatsQuery(message.body):
		returnMessage = getApStatsForNick(message.sendingNick)
		messages.append(ircMessage().newRoomMessage(returnMessage))

	irc.sendMessages(messages)
