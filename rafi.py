from ircBase import *
import modules.baseModule as baseModule
import modules.redditModule as redditModule
import modules.twssModule as twssModule
import modules.weatherModule as weatherModule
import modules.imageModule as imageModule
import modules.ircCommandModule as ircCommandModule
import modules.smsModule as smsModule
import modules.apTrackingModule as apTrackingModule
import modules.fourdeezModule as fourdeezModule

irc = IrcConnection.newConnection()

#Main Bot Loop ---------------------------------
#-----------------------------------------------
while True:
   connectionStillUp = irc.respondToServerMessages()
 
   #Reconnect if needed 
   if not connectionStillUp:
      irc = IrcConnection.newConnection()
      continue
 
   #Command Modules
   baseModule.main(irc)
   redditModule.main(irc)
   # twssModule.main(irc)
   weatherModule.main(irc)
   imageModule.main(irc)
   smsModule.main(irc)
   apTrackingModule.main(irc)
   fourdeezModule.main(irc)

   print irc.lastMessage().rawMessage
