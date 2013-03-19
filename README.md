# RafiBot: Module Based IRC Bot

RafiBot was designed to be easily extendable so that we could make him do anything that Python can do.  Please add to the framework I've made for Rafi and create new modules for him.

## Installation

After cloning this repo you are almost ready to run Rafi!  First, make sure you have the correct software on your system.  If you are running Arch linux then you can run the installation script found at `installation/arch_install.sh` to install all the necessary packages needed to run Rafi.  If you plan on not using any of the modules included with Rafi and only want to write your own then all you need is python 2.7.x

* Python 2.7.x
* Python MySql module (needed for the apTrackingModule)
* Python BeautifulSoup4 module (needed for several modules)
* MySql (needed for the apTrackingModule)
* Of course git :P

After these are installed copy the configuration file templates found in `installation/configTemplates` to a folder named `configs` in Rafi's root folder.  These configuration files are templates and will need to be edited for your specific environment before Rafi will run properly.
Now you are good to go!  Just run `python2 ./rafi.py` and watch him rage!

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

Your module should have a main function that takes an `ircConnection` object as a parameter.  After that it is really up to you.  The baseModule module is fairly straight forward and can be used as a guide to get the hang of making new modules.

After your module is finished add it to Rafi's main loop in the block with the other modules.

    yourModuleName.main(irc)

#### Something to note

`lastMessage(self)`  This is a method of the IRC connection.  It returns to you the last thing said in the room.  You will probably want to have it at the very top of your module's `main(irc)` function because so many of the activity cases rely on knowing the message you wish to respond to.  The ircBase module does this, and can be used as a guide.

### Detecting IRC activity

The ircMessage class provides a number of simple cases that represent IRC activity that your module can respond to.  Feel free to add more.  Examples of all of the cases are in the baseModule module.
The ircConnection class has the method `noRoomActivityForTime(timeInSeconds)` that can also be used to do something if the room has been idle for a certain period of time.

`message.isBotCommand`  This case is true if the IRC activity that the module is responding to is a command sent to Rafi.  Commands are in the format `!RafiBot <command>`.  The bot command that this message contains can be accessed with `message.botCommand` and used to determine the course of action to take.  If there are additional arguments to the command following the bot command they can be found in `message.botCommandArguments`.

`message.containsKeyword(aKeyword)` This case is true if the IRC activity that the module is responding to is a message containing a keyword.  This message doesn't need to be directed at Rafi and will also respond if the keyword is part of another word.  So if you make Rafi respond to the letter "a" any word with "a" in it will trigger this case.

`message.containsKeywords(someKeywords)`  This case is true if the IRC activity that the module is responding to is a message containing all given keywords.  Like the above case, the message doesn't need to directed at Rafi and keywords can be parts of larger words.  This can be used to make Rafi respond to more specific messages.  The argument `someKeywords` is an array of strings.

`ircConnection.noRoomActivityForTime(timeInSeconds)`  This case is true when there has been no activity in the room for certain amount of time.  Unlike all of the above cases, the first argument here is the IRC connection itself, not a message.  The argument `timeInSeconds` is obviously the amount of time in seconds since anyone has said anything (including Rafi).  This time is not exact because Rafi will only check the time elapsed during IRC PING requests.  So the time given is really a minimum amount of time since last activity.  When Rafi actually responds is uncertain, but it will be sometime after that amount of time has elapsed.

`message.isRoomMessage`  This case is true if the message was a private message intended for the room.  This can be used to filter out server messages or private messages directed to Rafi. The body of the message can be accessed with `message.body`.

`message.sendingNick`  This property is the nick that the message came from.  This can be used to respond to different people in different ways, or reply to people privatley.

`message.body`  This returns the actual content of a message (the part that usual gets shown in IRC clients).  It does not include details like the room, the nick, or any server information that can be found in the normal message.  Usefull for responding to the text that a person types.

`message.hasLinks`  This case is true if the IRC message contains any links. An array of links in a message can be accessed with `message.links`.

`message.rawMessage`  This is the raw text of a message including all details like the room, the nick, and any server information.  Most of the usefull information in this string has already been parsed out into properties of messages, but if you wanted more exact control you could parse this yourself.

`message.isServerMessage`  This case is true if the IRC message was a message for the server (JOIN, PART, etc.).  If it is then the `message.body` property will be empty and anything you wish to do with the message must be done against the `message.rawMessage` property.

### Responding to IRC activity

Once a case is satisfied you will want Rafi to do something.  To send a message back to the server you must first construct an `ircMessage` object.  To construct a new message object you should use one of the constructor methods in the `ircMessage` class.

`ircMessage().newRoomMessage(anIrcConnection, theMessageBody, aRoom = None, offRecord = False)`  This will construct a new message to be sent to a room.  You must pass in the `ircConnection` object you want the message to be sent out on and the body of the message as you want it to appear in the room.  The room to send the message to is optional, if you do not specify one it sends the message to the default room of the passed in `ircConnection`.  You can also specify if you would like the message kept off the record.  Off the record messages will not be logged by Rafi and therefore will not be visible when requesting the room history.

`ircMessage().newPrivateMessage(anIrcConnection, theMessageBody, aRecievingNick, offRecord = True)`  This will construct a new message to be sent to a specific nick.  You must pass in the `ircConnection` object you want the message to be sent out on, the body of the message, and the nick you would like to recieve the message.  You can also specify if you would like the message on the record, by default private messages are off the record and therefore not logged.

`ircMessage().newServerMessage(anIrcConnection, theMessageBody, offRecord = True)`  This will construct a new message to be sent to the server.  You must pass in the `ircConnection` object you want the message to be sent out on, and the body of the message.  This message is used to send commands like QUIT to the server.  By default server commands are off the record, but you can choose to log it if you would like.

After an `ircMessage` object is constructed you can send it by useing the `message.send()` method.  This will send the message out on the `ircConnection` that was passed in during the message creation.  So to construct and send a message to the room you would do something like this: `ircMessage().newRoomMessage(irc, 'My first message').send()`
More examples of different message types can be found in the baseModule module.
