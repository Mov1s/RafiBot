from ircBase import *
from bottle import route, run, template
import apTrackingModule
import MySQLdb as mdb
import time
import datetime
import ConfigParser
from multiprocessing import Process

config = ConfigParser.SafeConfigParser()
config.read('configs/ircBase.conf')

CONST_DB_USER = config.get('MySql', 'username')
CONST_DB_PASSWORD = config.get('MySql', 'password')

CONST_MODULE = None

class AndroidServiceModule(IrcModule):

    @route('/<action>/<name>')
    def index(action,name):
        returnMessage = ''
        if(action=='stats'):
            statsMessage = apTrackingModule.getApStatsForNick(mdb.connect('localhost',CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot'), name)
            returnMessage = '{'
            if 'drinking' in statsMessage:
                returnMessage += '"currentAP":"true",'
            returnMessage += '"message":"' + statsMessage + '"}'
        if(action=='start'):
            returnMessage = '{"message":"' + apTrackingModule.startTrackingApForNick(mdb.connect('localhost',CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot'), name) + '"}'
        if(action=='stop'):
            returnMessage = '{"message":"' + apTrackingModule.stopTrackingApForNick(mdb.connect('localhost',CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot'), name) + '"}'
        return returnMessage

    t = Process(target=run, kwargs=dict(host='0.0.0.0', port=31337))
    t.start()

    def defineResponses(self):
        print self
        print self.ircBot
        global CONST_MODULE
        CONST_MODULE = self
