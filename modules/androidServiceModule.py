from ircBase import *
from bottle import route, run, template
import apTrackingModule
import time
import datetime
from multiprocessing import Process

def setup_server(theHost, thePort, theModule):
    route('/<action>/<name>')(theModule.index)
    run(host=theHost, port=thePort)

class AndroidServiceModule(IrcModule):

    def defineResponses(self):
        t = Process(target=setup_server, kwargs=dict(theHost='0.0.0.0', thePort=31337, theModule=self))
        t.start()

    def index(self, action, name):

        print self
        #Get the current database connection from the running module
        module_database_connection = self.ircBot.databaseConnection()

        #Perform ap tracking action for stats
        returnMessage = ''
        if(action=='stats'):
            statsMessage = apTrackingModule.getApStatsForNick(module_database_connection, name)
            returnMessage = '{'
            if 'drinking' in statsMessage:
                returnMessage += '"currentAP":"true",'
            returnMessage += '"message":"' + statsMessage + '"}'

        #Perform ap tracking action for start
        if(action=='start'):
            startMessage = apTrackingModule.startTrackingApForNick(module_database_connection, name)
            if 'Bottoms' in startMessage:
                self.ircBot.irc.sendMessage(IrcMessage.newRoomMessage(name + ' has started drinking an AP. ' + startMessage))
            returnMessage = '{"message":"' + startMessage + '"}'

        #Perform ap tracking action for stop
        if(action=='stop'):
            stopMessage = apTrackingModule.stopTrackingApForNick(module_database_connection, name)
            if 'took' in stopMessage:
                self.ircBot.irc.sendMessage(IrcMessage.newRoomMessage(stopMessage.replace('you',name)))
            returnMessage = '{"message":"' + stopMessage + '"}'
        return returnMessage
