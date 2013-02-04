from ircBase import *
import MySQLdb as mdb
import time

#Check if message is a request to start tracking AP
def apStartQuery(aMessageBody):
	expression = re.compile('(track ap start)', re.IGNORECASE)
	match = expression.match(aMessageBody)
	return True if match else False

#Check if message is a request to stop tracking AP
def apStopQuery(aMessageBody):
	expression = re.compile('(track ap stop)', re.IGNORECASE)
	match = expression.match(aMessageBody)
	return True if match else False

#Start tracking the time of an AP
def startTrackingApForNick(aMessageNick):
	conn = mdb.connect('localhost', '', '', 'moduleApTracker')
	cursor = conn.cursor()

	#Don't allow the user to start another AP if they still have one open
	cursor.execute("SELECT * FROM ApRecord ar WHERE ar.nick = %s and ar.endTime IS NULL", (aMessageNick))
	if cursor.rowcount != 0:
		return False

	#Start a new AP record
	startTime = time.strftime('%Y-%m-%d %H:%M:%S')
	cursor.execute("INSERT INTO ApRecord (nick, startTime) VALUES (%s, %s)", (aMessageNick, startTime))
	conn.commit()

	return True

#Stop tracking the current AP
def stopTrackingApForNick(aMessageNick):
	conn = mdb.connect('localhost', '', '', 'moduleApTracker')
	cursor = conn.cursor()

	#Don't allow the user to stop AP if they don't have one started
	duration = None
	cursor.execute("SELECT * FROM ApRecord ar WHERE ar.nick = %s and ar.endTime IS NULL", (aMessageNick))
	if cursor.rowcount != 0:
		result = cursor.fetchall()
		startTime = result[0][2]

		endTime = time.strftime('%Y-%m-%d %H:%M:%S')
		duration = '1'

		#Close AP record
		cursor.execute("UPDATE ApRecord SET endTime = %s, duration = %s", (endTime, duration))
		conn.commit()
	else:
		return False

	return True

def main(irc):
	message = irc.lastMessage()

	if message.body == None:
		return

	if apStartQuery(message.body):
		succeed = startTrackingApForNick(message.sendingNick)
		if not succeed:
			ircMessage().newRoomMessage(irc, 'You are already drinking an AP').send()
	elif apStopQuery(message.body):
		succeed = stopTrackingApForNick(message.sendingNick)
		if not succeed:
			ircMessage().newRoomMessage(irc, 'You haven\'t started drinking an AP').send()