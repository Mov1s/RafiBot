from ircBase import *
import modules.imageModule as imageModule
import modules.redditModule as redditModule
import modules.apTrackingModule as apTrackingModule
import modules.fourdeezModule as fourdeezModule
import modules.weatherModule as weatherModule
import modules.smsModule as smsModule

rafi = IrcBot()
rafi.attachModule(imageModule.ImageModule())
rafi.attachModule(redditModule.RedditModule())
rafi.attachModule(apTrackingModule.ApTrackingModule())
rafi.attachModule(fourdeezModule.FourdeezModule())
rafi.attachModule(weatherModule.WeatherModule())
rafi.attachModule(smsModule.SmsModule())
rafi.run()
