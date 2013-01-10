import ircBase
import modules.baseModule as baseModule
# import modules.redditModule as redditModule
# import modules.twssModule as twssModule
# import modules.weatherModule as weatherModule
# import modules.imageModule as imageModule

irc = ircBase.ircConnection().newConnection()

#Main Bot Loop ---------------------------------
#-----------------------------------------------
while True:
   irc.respondToServerMessages()
   
   #Command Modules
   #baseModule.main(irc)
   # redditModule.main(irc)
   # twssModule.main(irc)
   # weatherModule.main(irc)
   # imageModule.main(irc)
   
   print irc.lastMessage().rawMessage
