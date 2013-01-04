import ircBase
import modules.baseModule as baseModule
import modules.redditModule as redditModule
import modules.twssModule as twssModule

irc = ircBase.createIrcConnection()

#Main Bot Loop ---------------------------------
#-----------------------------------------------
while True:
   irc = ircBase.respondToServerMessages(irc)
   
   #Command Modules
   baseModule.main(irc)
   redditModule.main(irc)
   twssModule.main(irc)
   
   print irc.lastMessage()