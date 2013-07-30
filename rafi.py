from ircBase import *
import modules.imageModule as imageModule
import modules.redditModule as redditModule

rafi = IrcBot()
rafi.attachModule(imageModule.ImageModule())
rafi.attachModule(redditModule.RedditModule())
rafi.run()
