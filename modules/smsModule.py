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

def getContactList():
	configFile = open('configs/smsConfig.conf','r')
	contactList = configFile.readlines()
	contactList = [x.replace('\n', '') for x in contactList]
	return contactList

def getContacts(contactList):
	contacts = ''
	for index, item in enumerate(contactList):
		if index%2 == 0 and index>=2:
			contacts += "| " + contactList[index]
	return contacts[1:]
	
@respondtoregex('(text)(' + getContacts(getContactList())  + ') (.*)')
def sendText(message, **extra_args):
	contactList = getContactList()
	contact = extra_args['match_group'][1]
	contact = contact.strip()
	text = extra_args['match_group'][2]
	try:
		sendMail(contactList,contact,"<" + message.sending_nick + "> " + text)
		return message.new_response_message("Text message sent to " + contact)
	except:
		return

@respondtoregex('(contact list)')
def printContactList(message, **extra_args):
	return message.new_response_message("Contacts in system:" + getContacts(getContactList()).replace("|",","))		

@respondtoidletime(0)
def readEmail (**extra_args):
	try:
		messages = []
		contactList = getContactList()
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
							attachment = payload[1]
							message = attachment.get_payload(decode=True)
						contact = contactList[getContactIndex(contactList, fromAddr[:10]) -1].split("|")
						if getContactIndex(contactList, fromAddr[:10]) <> -1:
							messages.append(IrcMessage.new_room_message("<" + contact[0] + "> " + message))
				typ, response = conn.store(num, '+FLAGS', r'(\Seen)')
		finally:
			try:
				conn.close()
				return messages
			except:
				pass
			conn.logout()
	except:
		return



def sendMail(contactList, to, text):
	fromAddr = contactList[0].strip()
	password = contactList[1].strip()

	toAddr = contactList[getContactIndex(contactList,to) + 1]	
	
	mailServer = smtplib.SMTP('smtp.gmail.com:587')
	mailServer.ehlo()
	mailServer.starttls()
	mailServer.ehlo()
	mailServer.login(fromAddr,password)
	mailServer.sendmail(fromAddr,toAddr,text)
	mailServer.close()


def getContactIndex (contactList, contact):
	for i, s in enumerate(contactList):
		if contact in s and i>=2:
			return i
	return -1


def extract_body(payload):
	if isinstance(payload,str):
		return payload
	else:
		return '\n'.join([extract_body(part.get_payload()) for part in payload])
