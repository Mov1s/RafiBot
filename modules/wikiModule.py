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

def upload_from_web(url):
    response = cStringIO.StringIO()
    c = pycurl.Curl()

    values = [("key", cfg.IMGUR_KEY),("image", url)]
    c.setopt(c.URL, "http://api.imgur.com/2/upload.xml")
    c.setopt(c.HTTPPOST, values)
    c.setopt(c.WRITEFUNCTION, response.write)
    c.perform()
    c.close()

    return response.getvalue()

def upload_web_img(url):
    xml = upload_from_web(url)
    o = untangle.parse(xml)
    url = o.upload.links.original.cdata

    return url


class WikiModule(IrcModule):
	def defineResponses(self):
		self.respondToRegex('(wiki)( me| ma)? (.*)', wikiParagraph)

def wikiParagraph(message, **extra_args):
    article= extra_args['matchGroup'][2]
    article = urllib.quote(article)

    html = urllib2.urlopen("http://en.wikipedia.org/wiki/" + article)
    soup = BeautifulSoup(html)
    paragraphs = soup.findAll('div', id="bodyContent")
    for paragraph in paragraphs:
        response = re.sub('\[[^\[]+?\]', '',strip_tags(paragraph.p))
    #response = re.sub('\[[^\[]+?\]', '',strip_tags(soup.find('div',id="bodyContent").p))
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    responses = tokenizer.tokenize(response)

    messages = []
    for sentence in responses:
        messages.append(IrcMessage.newPrivateMessage(sentence, message.sendingNick))
    try:
        imgs = soup.findAll("table", {"class":"infobox"})
        for img in imgs:
            imgUrl = 'http:' + img.findAll("tr")[1].find("img")['src']
            messages.append(IrcMessage.newPrivateMessage(upload_web_img(imgUrl), message.sendingNick))
    except:
        messages.append(IrcMessage.newPrivateMessage('Unable to grab picture.', message.sendingNick))


    return messages
