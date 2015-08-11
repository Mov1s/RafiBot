from ircBase import *
import modules.imageModule
import modules.baseModule
import modules.apTrackingModule
import modules.dogecoinModule
import modules.errorLoggingModule
import modules.fourdeezModule
import modules.redditModule
import modules.smsModule
import modules.weatherModule
import modules.wikiModule
import modules.androidServiceModule

#Start a backgrounded AP server
api = modules.androidServiceModule.AndroidService()
api.start()

#Start Rafi
rafi = IrcBot.shared_instance()
rafi.run()

#Stop the backgrounded AP server
api.stop()
