from ircBase import *
import modules.imageModule as imageModule
import modules.redditModule as redditModule
import modules.apTrackingModule as apTrackingModule
import modules.fourdeezModule as fourdeezModule

rafi = IrcBot()
rafi.attachModule(imageModule.ImageModule())
rafi.attachModule(redditModule.RedditModule())
rafi.attachModule(apTrackingModule.ApTrackingModule())
rafi.attachModule(fourdeezModule.FourdeezModule())
rafi.run()
