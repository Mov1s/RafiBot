from ircBase import *

def main(irc):
  	message = irc.lastMessage()
	
	#Check for irc command. JOIN or NICK only
	if messageIsBotCommand(message, 'irc'):
		if(messageContainsKeyword(message.lower(), 'join') or messageContainsKeyword(message.lower(), 'nick')):
			#Get IRC command sent 
			command = message[message.rfind('irc') + 3:]
			
			#Sent command to IRC server
			irc.sendCommand(command)

