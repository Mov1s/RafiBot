from ircBase import *
import MySQLdb as mdb
import time
import datetime

class ApTrackingModule(IrcModule):

  def defineResponses(self):
    self.respondToRegex('(track ap start)', self.ap_start_response)
    self.respondToRegex('(track ap stop)', self.ap_stop_response)
    self.respondToRegex('(track ap stats)', self.ap_stats_response)

  def ap_start_response(self, message, **extra_args):
    """Start tracking an AP and return a confirmation message."""
    returnMessage = startTrackingApForNick(self.ircBot.databaseConnection(), message.sendingNick)
    return message.newResponseMessage(returnMessage)

  def ap_stop_response(self, message, **extra_args):
    """Stop track the last started AP and return a confirmation message."""
    returnMessage = stopTrackingApForNick(self.ircBot.databaseConnection(), message.sendingNick)
    return message.newResponseMessage(returnMessage)

  def ap_stats_response(self, message, **extra_args):
    """Gather stats on the all APs and return them"""
    returnMessage = getApStatsForNick(self.ircBot.databaseConnection(), message.sendingNick)
    return message.newResponseMessage(returnMessage)


#------------------------------------------------------------------
#MySQL AP Methods
#------------------------------------------------------------------

#Start tracking the time of an AP
#(in)aMessageNick - The nick to start tracking for
#(out) The message to print to the room
def startTrackingApForNick(aDatabaseConnection, aMessageNick):
  cursor = aDatabaseConnection.cursor()
  
  #Get the UserId for this nick
  cursor.execute("SELECT userId FROM rafiBot.Nicks WHERE nick = %s", (aMessageNick,))
  if cursor.rowcount == 0:
    return 'This nick is not linked to a registered user'
  userId = cursor.fetchall()[0][0]

  #Don't allow the user to start another AP if they still have one open
  cursor.execute("SELECT id FROM moduleApTracker.ApRecord ar WHERE ar.userId = %s and ar.endTime IS NULL", (userId,))
  if cursor.rowcount != 0:
    return 'You are already drinking an AP'

  #Start a new AP record
  startTime = time.strftime('%Y-%m-%d %H:%M:%S')
  cursor.execute("INSERT INTO moduleApTracker.ApRecord (userId, startTime) VALUES (%s, %s)", (userId, startTime,))
  aDatabaseConnection.commit()
  cursor.close()

  return 'Bottoms up!'

#Stop tracking the current AP
#(in)aMessageNick - The nick to stop tracking for
#(out) The message to print to the room
def stopTrackingApForNick(aDatabaseConnection, aMessageNick):
  cursor = aDatabaseConnection.cursor()

  #Get the UserId for this nick
  cursor.execute("SELECT userId FROM rafiBot.Nicks WHERE nick = %s", (aMessageNick,))
  if cursor.rowcount == 0:
    return 'This nick is not linked to a registered user'
  userId = cursor.fetchall()[0][0]

  #Don't allow the user to stop AP if they don't have one started
  cursor.execute("SELECT id, unix_timestamp(startTime) FROM moduleApTracker.ApRecord ar WHERE ar.userId = %s and ar.endTime IS NULL", (userId,))
  if cursor.rowcount != 0:
    result = cursor.fetchall()
    startTime = result[0][1]

    #Calculate the AP duration
    endTime = time.strftime('%Y-%m-%d %H:%M:%S')
    endTimeInt = time.time()
    duration = endTimeInt - startTime

    #Close AP record
    recordId = result[0][0]
    cursor.execute("UPDATE moduleApTracker.ApRecord SET endTime = %s, duration = %s WHERE id = %s", (endTime, duration, recordId,))
    aDatabaseConnection.commit()
    cursor.close()

    return 'That AP took you ' + str(datetime.timedelta(seconds = duration))
  else:
    return 'You haven\'t started drinking an AP'

#Get a user's AP stats
#(in)aMessageNick - The nick to report stats for
#(out) The message to print to the room
def getApStatsForNick(aDatabaseConnection, aMessageNick):
  cursor = aDatabaseConnection.cursor()

  print aMessageNick

  #Get the UserId for this nick
  cursor.execute("SELECT userId FROM rafiBot.Nicks WHERE nick = %s", (aMessageNick,))
  if cursor.rowcount == 0:
    return 'This nick is not linked to a registered user'
  userId = cursor.fetchall()[0][0]

  statMessage = ''
  #Get the total time of all complete APs and the count of how many have been drank
  cursor.execute("SELECT COUNT(id), SUM(duration) FROM moduleApTracker.ApRecord ar WHERE ar.userId = %s and ar.endTime IS NOT NULL", (userId,))
  result = cursor.fetchall()
  totalAps = result[0][0]
  if totalAps != 0:
    totalDuration = result[0][1]
    formatedDuration = str(datetime.timedelta(seconds = int(totalDuration)))

    statMessage = 'You have drank ' + str(totalAps) + ' AP(s) for a total time of ' + formatedDuration + '.  '

  #Check to see if there are any open APs and report stats on those
  cursor.execute("SELECT unix_timestamp(startTime) FROM moduleApTracker.ApRecord ar WHERE ar.userId = %s and ar.endTime IS NULL", (userId,))
  if cursor.rowcount != 0:
    result = cursor.fetchall()
    startTime = result[0][0]
    duration = time.time() - startTime

    statMessage += 'You have been drinking your current AP for ' + str(datetime.timedelta(seconds = duration)) + '.'
  
  #If there are no stats report that
  if statMessage == '':
    statMessage = 'Nothing to report'

  cursor.close()
  return statMessage
