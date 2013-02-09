# -*- coding:utf8 -*-
from ircBase import *
import smtplib 
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
import imaplib
import email


CONST_CONTACT = 2
CONST_MESSAGE = 3


def extract_body(payload):
	if isinstance(payload,str):
		return payload
	else:
		return '\n'.join([extract_body(part.get_payload()) for part in payload])



def readEmail (irc, contactList):
	try:
		conn = imaplib.IMAP4_SSL("imap.gmail.com", 993)
		conn.login(contactList[0],contactList[1])
		conn.select()
		typ, data = conn.search(None, 'UNSEEN')
		try:
			for num in data[0].split():
				typ, msg_data = conn.fetch(num, '(RFC822)')
				for response_part in msg_data:
					if isinstance(response_part, tuple):
						msg = email.message_from_string(response_part[1])
						fromAddr = msg['from']
						payload=msg.get_payload()
						message=extract_body(payload)
						if len(payload) == 2:
							print("Hello, world!")
							attachment = payload[1]
							message = attachment.get_payload(decode=True)
						contact = contactList[getContactIndex(contactList, fromAddr[:10]) -1].split("|")
						if getContactIndex(contactList, fromAddr[:10]) <> -1:	
							ircMessage.newRoomMessage(irc, "<" + contact[0] + "> " + message).send()
				typ, response = conn.store(num, '+FLAGS', r'(\Seen)')
		finally:
			try:
				conn.close()
			except:
				pass
			conn.logout()
	except:
		return


def getContactIndex (contactList, contact):
	for i, s in enumerate(contactList):
		if contact in s:
			return i
	return -1


def getContactList():
	configFile = open('configs/smsConfig','r')
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
	
	toAddr = contactList[getContactIndex(contactList,to) + 1]	

	mailServer = smtplib.SMTP('smtp.gmail.com:587')
	mailServer.ehlo()
	mailServer.starttls()
	mailServer.ehlo()
	mailServer.login(fromAddr,password)
	mailServer.sendmail(fromAddr,toAddr,text)
	mailServer.close()

	
def getQuery(contactList, message, messagePart):
	stringMatch = "(text|txt)(" + getContacts(contactList) + ") (.*)"
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
	readEmail(irc, contactList)
	if message.botCommand == "contacts":
		ircMessage.newRoomMessage(irc, "Contacts in system:" + getContacts(contactList).replace("|",",")).send()		
	if message.body != None:
		text = getQuery(contactList,message.body,CONST_MESSAGE)
		if text:
			print getQuery(contactList,message.body,CONST_CONTACT)
			contact = getQuery(contactList,message.body,CONST_CONTACT)
			if contact:
				try:
					print message.sendingNick
					sendMail(contactList,contact,"<" + message.sendingNick + "> " + text)
					ircMessage.newRoomMessage(irc, "Text message sent to " + contact).send()
				except:
					return
			else:
				ircMessage.newRoomMessage(irc, "Does not match any known contact.").send()
