from ircBase import *
from bottle import route, run, template
import apTrackingModule
import time
import datetime
import ConfigParser
from multiprocessing import Process

config = ConfigParser.SafeConfigParser()
config.read('configs/ircBase.conf')

CONST_DB_USER = config.get('MySql', 'username')
CONST_DB_PASSWORD = config.get('MySql', 'password')

def setup_server(theHost, thePort, theModule):
    route('/<action>/<name>')(theModule.index)
    run(host=theHost, port=thePort)

class AndroidServiceModule(IrcModule):

    def defineResponses(self):
        t = Process(target=setup_server, kwargs=dict(theHost='0.0.0.0', thePort=31337, theModule=self))
        t.start()

    def index(self, action, name):
        #Open Database Connection
        databaseConnection = mdb.connect('localhost', CONST_DB_USER, CONST_DB_PASSWORD)

        #Perform ap tracking action for stats
        returnMessage = ''
        if(action=='stats'):
            statsMessage = apTrackingModule.getApStatsForNick(databaseConnection, name)
            returnMessage = '{'
            if 'drinking' in statsMessage:
                returnMessage += '"currentAP":"true",'
            returnMessage += '"message":"' + statsMessage + '"}'

        #Perform ap tracking action for start
        if(action=='start'):
            startMessage = apTrackingModule.startTrackingApForNick(databaseConnection, name)
            if 'Bottoms' in startMessage:
                self.ircBot.irc.sendMessage(IrcMessage.newRoomMessage(name + ' has started drinking an AP. ' + startMessage))
            returnMessage = '{"message":"' + startMessage + '"}'

        #Perform ap tracking action for stop
        if(action=='stop'):
            stopMessage = apTrackingModule.stopTrackingApForNick(databaseConnection, name)
            if 'took' in stopMessage:
                self.ircBot.irc.sendMessage(IrcMessage.newRoomMessage(stopMessage.replace('you',name)))
            returnMessage = '{"message":"' + stopMessage + '"}'

        #Close Database Connection
        databaseConnection.close()

        return returnMessage
