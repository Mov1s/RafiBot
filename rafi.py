import ircBase
import modules.baseModule as baseModule
import modules.redditModule as redditModule
import modules.imageModule as imageModule

irc = ircBase.createIrcConnection()

#Main Bot Loop ---------------------------------
#-----------------------------------------------
while True:
   irc = ircBase.respondToServerMessages(irc)
   
   #Command Modules
   baseModule.main(irc)
   redditModule.main(irc)
   imageModule.main(irc)
   
   print irc.lastMessage()