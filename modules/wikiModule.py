# -*- coding:utf8 -*-
from ircBase import *
import urllib2
import urllib
from bs4 import BeautifulSoup
import ConfigParser
import json
from HTMLParser import HTMLParser
import nltk.data
import re
from jabbapylib import config as cfg
import pycurl
import untangle
import cStringIO

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(str(html))
    return s.get_data()


class WikiModule(IrcModule):
	def defineResponses(self):
		self.respondToRegex('(wiki)( me| ma)? (.*)', wikiParagraph)

def wikiParagraph(message, **extra_args):
    article= extra_args['matchGroup'][2]
    article = urllib.quote(article)
    articleUrl = "http://en.wikipedia.org/wiki/" + article

    html = urllib2.urlopen(articleUrl)
    soup = BeautifulSoup(html)
    paragraphs = soup.findAll('div', id="bodyContent")
    for paragraph in paragraphs:
        response = re.sub('\[[^\[]+?\]', '',strip_tags(paragraph.p))
    #response = re.sub('\[[^\[]+?\]', '',strip_tags(soup.find('div',id="bodyContent").p))
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    responses = tokenizer.tokenize(response)

    messages = []
    messages.append(IrcMessage.newRoomMessage(articleUrl))
    for sentence in responses:
        messages.append(IrcMessage.newRoomMessage(sentence))
    try:
        imgs = soup.findAll("table", {"class":"infobox"})
        for img in imgs:
            imgUrl = 'http:' + img.findAll("tr")[1].find("img")['src']
            messages.append(IrcMessage.newRoomMessage(imgUrl))
    except:
        messages.append(IrcMessage.newRoomMessage('Unable to grab picture.'))


    return messages
