from ircBase import *
import modules.imageModule as imageModule

rafi = IrcBot()
rafi.attachModule(imageModule.ImageModule())
rafi.run()
