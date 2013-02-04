from ircBase import *
import MySQLdb as mdb
import time
import datetime

CONST_DB_USER = ''
CONST_DB_PASSWORD = ''

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
	conn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'moduleApTracker')
	cursor = conn.cursor()

	#Don't allow the user to start another AP if they still have one open
	cursor.execute("SELECT * FROM ApRecord ar WHERE ar.nick = %s and ar.endTime IS NULL", (aMessageNick))
	if cursor.rowcount != 0:
		return 'You are already drinking an AP'

	#Start a new AP record
	startTime = time.strftime('%Y-%m-%d %H:%M:%S')
	cursor.execute("INSERT INTO ApRecord (nick, startTime) VALUES (%s, %s)", (aMessageNick, startTime))
	conn.commit()

	return 'Bottoms up!'

#Stop tracking the current AP
#(in)aMessageNick - The nick to stop tracking for
#(out) The message to print to the room
def stopTrackingApForNick(aMessageNick):
	conn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'moduleApTracker')
	cursor = conn.cursor()

	#Don't allow the user to stop AP if they don't have one started
	cursor.execute("SELECT id, unix_timestamp(startTime) FROM ApRecord ar WHERE ar.nick = %s and ar.endTime IS NULL", (aMessageNick))
	if cursor.rowcount != 0:
		result = cursor.fetchall()
		startTime = result[0][1]

		#Calculate the AP duration
		endTime = time.strftime('%Y-%m-%d %H:%M:%S')
		endTimeInt = time.time()
		duration = endTimeInt - startTime

		#Close AP record
		recordId = result[0][0]
		cursor.execute("UPDATE ApRecord SET endTime = %s, duration = %s WHERE id = %s", (endTime, duration, recordId))
		conn.commit()

		return 'That AP took you ' + str(datetime.timedelta(seconds = duration))
	else:
		return 'You haven\'t started drinking an AP'

#Get a user's AP stats
#(in)aMessageNick - The nick to report stats for
#(out) The message to print to the room
def getApStatsForNick(aMessageNick):
	conn = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD, 'moduleApTracker')
	cursor = conn.cursor()

	statMessage = ''
	#Get the total time of all complete APs and the count of how many have been drank
	cursor.execute("SELECT COUNT(id), SUM(duration) FROM ApRecord ar WHERE ar.nick = %s and ar.endTime IS NOT NULL", (aMessageNick))
	result = cursor.fetchall()
	totalAps = result[0][0]
	if totalAps != 0:
		totalDuration = result[0][1]
		formatedDuration = str(datetime.timedelta(seconds = int(totalDuration)))

		statMessage = 'You have drank ' + str(totalAps) + ' AP(s) for a total time of ' + formatedDuration + '.  '

	#Check to see if there are any open APs and report stats on those
	cursor.execute("SELECT unix_timestamp(startTime) FROM ApRecord ar WHERE ar.nick = %s and ar.endTime IS NULL", (aMessageNick))
	if cursor.rowcount != 0:
		result = cursor.fetchall()
		startTime = result[0][0]
		duration = time.time() - startTime

		statMessage += 'You have been drinking your current AP for ' + str(datetime.timedelta(seconds = duration)) + '.'
	
	#If there are no stats report that
	if statMessage == '':
		statMessage = 'Nothing to report'

	return statMessage

def main(irc):
	message = irc.lastMessage()

	#Needs message body
	if message.body == None:
		return

	#Start tracking an AP
	if apStartQuery(message.body):
		returnMessage = startTrackingApForNick(message.sendingNick)
		ircMessage().newRoomMessage(irc, returnMessage).send()
	#Stop tracking an AP
	elif apStopQuery(message.body):
		returnMessage = stopTrackingApForNick(message.sendingNick)
		ircMessage().newRoomMessage(irc, returnMessage).send()
	#Print the stats for AP
	elif apStatsQuery(message.body):
		returnMessage = getApStatsForNick(message.sendingNick)
		ircMessage().newRoomMessage(irc, returnMessage).send()