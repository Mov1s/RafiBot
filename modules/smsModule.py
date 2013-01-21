# -*- coding:utf8 -*-
from ircBase import *
import smtplib 
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText




def sendMail(to, text):
	fromAddr = "phyll1s.rafibot@gmail.com"
	password = "qwerty4u"

	mailServer = smtplib.SMTP('smtp.gmail.com:587')
	mailServer.ehlo()
	mailServer.starttls()
	mailServer.ehlo()
	mailServer.login(fromAddr,password)
	mailServer.sendmail(fromAddr,to,text)
	mailServer.close()


def getQuery(message):
	expression = re.compile('(text|txt)( madsen| phyll1s| luke| stilts| jimmy| jimjim| mov1s| popa)? (.*)', re.IGNORECASE)
	match = expression.match(message)
	if match:
		return match.group(3) 
	else:
		return None
	
def getContact(message):
	expression = re.compile('(text|txt)( madsen| phyll1s| luke| stilts| jimmy| jimjim| mov1s| popa)? (.*)', re.IGNORECASE)
	match = expression.match(message)
	if match:
		return match.group(2) 
	else:
		return None
	

def main(irc):
  	message = irc.lastMessage()
	
	if message.body != None:
		text = getQuery(message.body)
		if text:
			contact = getContact(message.body)
			if contact:
				if contact.lower().find('madsen') <> -1:
					try:
						sendMail("5178813592@vtext.com",text)
						ircMessage.newRoomMessage(irc, "Text message sent to" + contact).send()
					except:
						return
				elif contact.lower().find('phyll1s') <> -1:
					try:
						sendMail("5179270394@vtext.com",text)
						ircMessage.newRoomMessage(irc, "Text message sent to" + contact).send()
					except:
						return
				elif (contact.lower().find('luke') <> -1) or (contact.lower().find('stilts') <> -1):
					try:
						sendMail("5176041672@vtext.com",text)
						ircMessage.newRoomMessage(irc, "Text message sent to" + contact).send()
					except:
						return
				elif (contact.lower().find('jimmy') <> -1) or (contact.lower().find('jimjim') <> -1):
					try:
						sendMail("2102964231@vtext.com",text)
						ircMessage.newRoomMessage(irc, "Text message sent to" + contact).send()
					except:
						return
				elif (contact.lower().find('popa') <> -1) or (contact.lower().find('mov1s') <> -1):
					try:
						sendMail("5172421175@messaging.sprintpcs.com",text)
						ircMessage.newRoomMessage(irc, "Text message sent to" + contact).send()
					except:
						return
			else:
				ircMessage.newRoomMessage(irc, "Does not match any known contact.").send()
