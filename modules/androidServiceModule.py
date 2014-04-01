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

class AndroidServiceModule(IrcModule):

    @route('/<action>/<name>')
    def index(action,name):
        returnMessage = ''
        if(action=='stat'):
            returnMessage = apTrackingModule.getApStatsForNick(mdb.connect('localhost',CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot'), name)
            print __IRCBOT__
        if(action=='start'):
            returnMessage = apTrackingModule.startTrackingApForNick(mdb.connect('localhost',CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot'), name)
        if(action=='stop'):
            returnMessage = apTrackingModule.stopTrackingApForNick(mdb.connect('localhost',CONST_DB_USER, CONST_DB_PASSWORD, 'rafiBot'), name)
        return returnMessage

    t = Process(target=run, kwargs=dict(host='0.0.0.0', port=31337))
    t.start()

    def defineResponses(self):
        print self
