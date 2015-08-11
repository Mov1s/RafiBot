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

class AndroidService:
    
    def __init__(self, host = '0.0.0.0', port = 31337):
        self.server_process = Process(target = run, kwargs = dict(host = host, port = port))
        
    def start(self):
        self.server_process.start()
    
    def stop(self):
       self.server_process.terminate()

@route('/<action>/<name>')
def index(action, name):
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
            IrcBot.shared_instance().send_message(IrcMessage.new_room_message(name + ' has started drinking an AP. ' + startMessage))
        returnMessage = '{"message":"' + startMessage + '"}'

    #Perform ap tracking action for stop
    if(action=='stop'):
        stopMessage = apTrackingModule.stopTrackingApForNick(databaseConnection, name)
        if 'took' in stopMessage:
            IrcBot.shared_instance().send_message(IrcMessage.new_room_message(stopMessage.replace('you',name)))
        returnMessage = '{"message":"' + stopMessage + '"}'

    #Close Database Connection
    databaseConnection.close()

    return returnMessage
