# -*- coding:utf8 -*-
from ircBase import *
import smtplib 
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText


CONST_CONTACT = 2
CONST_MESSAGE = 3


def getContactList():
	configFile = open('config/smsConfig','r')
	contactList = configFile.readlines()
	contactList = [x.replace('\n', '') for x in contactList]

	return contactList

def getContacts(contactList):
	contacts = ''
	for index, item in enumerate(contactList):
		if index%2 == 0 and index>=2:
			contacts += "| " + contactList[index]
	return contacts[1:]
	

def sendMail(contactList, to, text):
	fromAddr = contactList[0]
	password = contactList[1]

	toAddr = contactList[contactList.index(to) + 1]	

	mailServer = smtplib.SMTP('smtp.gmail.com:587')
	mailServer.ehlo()
	mailServer.starttls()
	mailServer.ehlo()
	mailServer.login(fromAddr,password)
	mailServer.sendmail(fromAddr,toAddr,text)
	mailServer.close()

	
def getQuery(contactList, message, messagePart):
	stringMatch = "(text|txt)(" + getContacts(contactList) + ")? (.*)"
	expression = re.compile(stringMatch, re.IGNORECASE)
	match = expression.match(message)
	if match:
		try:
			return match.group(messagePart).strip()
		except:
			return None
	else:
		return None
	

def main(irc):
 	message = irc.lastMessage()
	contactList = getContactList()
	if message.botCommand == "contacts":
		ircMessage.newRoomMessage(irc, "Contacts in system:" + getContacts(contactList).replace("|",",")).send()		
	if message.body != None:
		text = getQuery(contactList,message.body,CONST_MESSAGE)
		if text:
			contact = getQuery(contactList,message.body,CONST_CONTACT)
			if contact:
				try:
					print message.sendingNick
					sendMail(contactList,contact,message.sendingNick + " says " + text)
					ircMessage.newRoomMessage(irc, "Text message sent to " + contact).send()
				except:
					return
			else:
				ircMessage.newRoomMessage(irc, "Does not match any known contact.").send()
