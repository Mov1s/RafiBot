# RafiBot: Module Based IRC Bot

RafiBot was designed to be easily extendable so that we could make him do anything that Python can do.  Please add to the framework I've made for Rafi and create new modules for him.

## For the future

Rafi's current capabilities are pretty limited but I would like to continue to develop him.  In the future I would like to see a few things that will help make our community development of him easier.
 
* Automatic deployment
    * Rafi currently responds to the update command, but all it does is make him quit with an update message so that I can restart him with new code.
    * I would like this eventually to make him quit, pull the latest code from git and then start himself back up, so that anyone can make changes and tell him to use them imediatley instead of having me restart him.
* Database migration
    * I intend to use a local mySQL database in some of the future modules, I would like to make a way for you guys to do the same.
    * This means you need a way to create your own database schema and have him apply it during deployment.

## Building a module

To create a new module simply create a new python file in the modules folder and include `from ircBase import *` in the module.

Your module should have a main function that takes an IRC object as a parameter.  After that it is really up to you.  The ircBase module is fairly straight forward and can be used as a guide to get the hang of making new modules.

After your module is finished add it to Rafi's main loop in the block with the other modules.

    yourModuleName.main(irc)

#### Something to note

`lastMessage(self)`  This is a method of the IRC connection.  It returns to you the last thing said in the room.  You will probably want to have it at the very top of your module's `main(irc)` function because so many of the activity cases rely on knowing the message you wish to respond to.  The ircBase module does this, and can be used as a guide.

### Detecting IRC activity

I've provided a number of simple cases that represent IRC activity that your module can respond to.  Feel free to add more.  Examples of all of the cases are in the ircBase module.
Note that most cases take the last IRC message as the first argument but some cases (like noRoomActivityForTime) take the IRC object as the first argument.

`messageIsBotCommand(aMessage, aCommand)` This case is true if the IRC activity that the module is responding to is a command sent to Rafi.  Commands are in the format `!RafiBot <command>`.  The argument `aCommand` is the command you want to check for.

`messageContainsKeyword(aMessage, aKeyword)` This case is true if the IRC activity that the module is responding to is a message containing a keyword.  This message doesn't need to be directed at Rafi and will also respond if the keyword is part of another word.  So if you make Rafi respond to the letter "a" any word with "a" in it will trigger this case.

`messageContainsKeywords(aMessage, someKeywords)`  This case is true if the IRC activity that the module is responding to is a message containing all given keywords.  Like the above case, the message doesn't need to directed at Rafi and keywords can be parts of larger words.  This can be used to make Rafi respond to more specific messages.  The argument `someKeywords` is an array of strings.

`noRoomActivityForTime(aConnection, timeInSeconds)`  This case is true when there has been no activity in the room for certain amount of time.  Unlike all of the above cases, the first argument here is the IRC connection itself, not a message.  The argument `timeInSeconds` is obviously the amount of time in seconds since anyone has said anything (including Rafi).  This time is not exact because Rafi will only check the time elapsed during IRC PING requests.  So the time given is really a minimum amount of time since last activity.  When Rafi actually responds is uncertain, but it will be sometime after that amount of time has elapsed.

`messageIsForRoom(aMessage)`  This case is true if the given message was a private message intended for the room.  This can be used to filter our server messages or private messages directed to Rafi.  It also filters out things that Rafi says, as those message don't show up as room messages.

`messageIsFromNick(aMessage, aNick)`  This case is true if the given message is from a certain nick.  This can be used to respond to different people in different ways.  It is not that flexible since it responds to hard coded nicks.

`bodyOfMessage(aMessage)`  This returns the actual content of a message (the part that usual gets shown in IRC clients).  It does not include details like the room, the nick, or any server information that can be found in the normal message.  Usefull for responding to the text that a person types.

### Responding to IRC activity

Once a case is satisfied you will want Rafi to do something.  I've provided only two basic avenues for him at the moment.

`sendMessage(self, aMessage)`  This is a method of the IRC connection.  It will have Rafi say something in the room.  The argument `self` is implicit in python and requires you to do nothing for it.  The argument `aMessage` is the message you would like Rafi to say in the room.

`sendCommand(self, aCommand)`  This is a method of the IRC connection.  It will have Rafi send a command to the server.  The argument `aCommand` is the command to send (QUIT, NICK, JOIN).
