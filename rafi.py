from ircBase import *
import modules.imageModule as imageModule

irc = IrcConnection.newConnection()

#Main Bot Loop ---------------------------------
#-----------------------------------------------
imgModule = imageModule.ImageModule()
while True:
   irc.respondToServerMessages()
   
   #Command Modules
   messages = []
   messages = messages + imgModule.do(irc.lastMessage())
   irc.sendMessages(messages)

   print irc.lastMessage().rawMessage
