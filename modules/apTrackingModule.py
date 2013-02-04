from ircBase import *
import MySQLdb as mdb
import time

#Check if message is a request to start tracking AP
def apStartQuery(aMessageBody):
	expression = re.compile('(track ap start)', re.IGNORECASE)
	match = expression.match(message)
	return True if match else False

#Check if message is a request to stop tracking AP
def apStopQuery(aMessageBody):
	expression = re.compile('(track ap stop)', re.IGNORECASE)
	match = expression.match(message)
	return True if match else False

#Start tracking the time of an AP
def startTrackingApForNick(aMessageNick):
	conn = mdb.connect('localhost', moduleSettings.mysqlUser, moduleSettings.mysqlPassword, 'moduleApTracker')
	cursor = conn.cursor()

	#Don't allow the user to start another AP if they still have one open
	cursor.execute("SELECT * FROM ApRecord ar WHERE ar.nick = %s and ar.endingTime = null", (aMessageNick))
	if cursor.rowcount != 0:
		ircMessage().newRoomMessage(irc, 'You are already drinking an AP').send()
		return False

	#Start a new AP record
	cursor.execute("INSERT INTO ApRecord (nick, startingTime) VALUES (%s, %s)", (aMessageNick, time.time()))
	conn.commit()

	return True

#Stop tracking the current AP
def stopTrackingApForNick(aMessageNick):
	conn = mdb.connect('localhost', moduleSettings.mysqlUser, moduleSettings.mysqlPassword, 'moduleApTracker')
	cursor = conn.cursor()

	#Don't allow the user to stop AP if they don't have one started
	duration = None
	cursor.execute("SELECT * FROM ApRecord ar WHERE ar.nick = %s and ar.endingTime = null", (aMessageNick))
	if cursor.rowcount != 0:
		result = cursor.fetchall()
		startTime = result[0][2]

		endTime = time.time()
		duration = endTime - startTime

		#Close AP record
		cursor.execute("UPDATE ApRecord SET endingTime = %s, duration = %s", (endTime, duration))
		conn.commit()
	else:
		ircMessage().newRoomMessage(irc, 'You haven\'t started drinking an AP').send()
		return False

	return True

def main(irc):
	message = irc.lastMessage()

	if apStartQuery(message.body):
		startTrackingApForNick(message.sendingNick)
	elif apStopQuery(message.body):
		stopTrackingApForNick(message.sendingNick)
