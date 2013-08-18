from ircBase import *
import modules.imageModule as imageModule
import modules.redditModule as redditModule
import modules.apTrackingModule as apTrackingModule

rafi = IrcBot()
rafi.attachModule(imageModule.ImageModule())
rafi.attachModule(redditModule.RedditModule())
rafi.attachModule(apTrackingModule.ApTrackingModule())
rafi.run()
