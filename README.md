# RafiBot: Module Based IRC Bot

RafiBot was designed to be easily extendable so that we could make him do anything that Python can do.  Please add to the framework I've made for Rafi and create new modules for him.

## Installation

After cloning this repo you are almost ready to run Rafi!  First, make sure you have the correct software on your system.  If you are running Arch linux then you can run the installation script found at `installation/arch_install.sh` to install all the necessary packages needed to run Rafi.  If you plan on not using any of the modules included with Rafi and only want to write your own then all you need is python 2.7.x

* Python 2.7.x
* Python MySql module (needed for the apTrackingModule and baseModule)
* Python BeautifulSoup4 module (needed for several modules)
* Python Google API Client (for image module)
* MySql (needed for the apTrackingModule and baseModule)
* Of course git :P

After these are installed copy the configuration file templates found in `installation/configTemplates` to a folder named `configs` in Rafi's root folder.  These configuration files are templates and will need to be edited for your specific environment before Rafi will run properly.
Now you are good to go!  Just run `python2 ./rafi.py` and watch him rage!

## For the future

Rafi's current capabilities are pretty limited but I would like to continue to develop him.  In the future I would like to see a few things that will help make our community development of him easier.
 
* Database migration
    * MySQL is used in a few modules and migration files have been written to apply the database changes needed to run modules but they are not automatic
    * This needs to be automated and have him apply the schema changes during deployment.

* Update recovery
    * If the update process fails Rafi fails to rejoin, meaning the error needs to be manually fixed and then he can be relaunched
    * It would be great if Rafi would revert the update and rejoin the server alerting users that the update failed

## Building a module

To create a new module simply create a new python file in the modules folder and import `ircBase`.

    from ircBase import *

A module is just a collection of functions we call 'actions' hooked up to certain triggers.  You can write a function and decorate it with one of the supported trigger events and it will be called when that event happens in IRC.  The `baseModule` module is fairly straight forward and can be used as a guide to get the hang of making new modules.

After your module is finished have the bot import it and its actions will be registered automatically.

### Actions

`ircBase` provides three basic triggers for IRC activity.  They can be used to decorate any python function and that function will become an action tied to an IRC event.  The triggers are outlined below.

##### @respondtoregex
An action decorated with this trigger will be called whenever an IRC message matches the given regex.  The message that triggered this action will be the first argument passed to your action.  Any number of other arguments may also be passed to this action containing other useful information about the event that triggered this action.

    @respondtoregex('hello rafi')
    def hello_response(message, **extra_args):
      """Respond to an IRC message containing the text 'hello rafi'."""
      return message.new_response_message("Hello")

##### @respondtobotcommand
An action decorated with this trigger will be called whenever a command is sent to your bot. A bot command is any message that starts with an exclamation point such as `!help`. The message that triggered this action will be the first argument passed to your action. Any number of other arguments may also be passed to this action containing other useful information about the event that triggered this action.

    @respondtobotcommand('help') 
    def help_response(message, **extra_args):
      """Respond to a bot command requesting help."""
      return message.new_response_message("I can not help you :(")

##### @respondtoidletime
An action decorated with this trigger will be called whenever there is no action in an IRC room for a given number of seconds.  There is nothing to pass to this action at the moment but it never hurts to be safe.

    @respondtoidletime(1800)
    def idle_response(**extra_args):
      """After 10 min with no room activity spice things up."""
      return IrcMessage.new_room_message('Cmon guys, liven up')

## Messages

Messages are everything, they are the events that trigger actions, and one way a module can respond to events. When an action is triggered from a message event you will get a reference to the message that caused the action.  A message has a number of useful flags and properties:

##### Flags

`message.is_bot_command`  This will be true if the message is a command sent to Rafi.  Commands are in the format `!<command>`.  The bot command that this message contains can be accessed with `message.bot_command` and used to determine the course of action to take.  If there are additional arguments to the command following the bot command they can be found in `message.bot_command_arguments`.

`message.is_off_record`  This will be true if the message was not added to the message log. All message activity in a room is logged, but messages sent by RafiBot can be excluded at the time of sending.  See 'Responding to IRC activity' for more information about on/off record messages.

`message.has_links`  This will be true if the message contains hyperlinks. All links found in a message can be easily accessed with `message.links`.

`message.is_private_message`  This will be true if the recieved message was sent directly to RafiBot, or if a sent message is directed to a user via private message.

`message.is_server_message`  This will be true if the recieved message is from the server, or if a sent message is directed at the server. These messages do not contain public chat information, but instead usually contain commands for the server to perform or information about server activity.

`message.is_room_message`  This will be true if the recieved message was sent to the room, or if a sent message is directed to the room.

`message.is_ping`  This will be true if the recieved message was a ping. These types of messages are sent periodically to make sure the server can still reach RafiBot. They will not be returned by the action decorators, so you will probably never interact with this type of message.

##### Properties

`message.sending_nick`  This is the nick that the message came from. This can be used to respond to different people in different ways, or reply to people privatley.

`message.body`  This returns the actual content of a message (the part that usually gets shown in IRC clients). It does not include details like the room, the nick, or any server information that can be found in the raw message.

`message.raw_message`  This is the raw message as it is recieved from, or sent to, the server. Most of the usefull information in this string has already been parsed out into properties of messages, but if you wanted more exact control you could parse this yourself.

`message.bot_command`  If the message is a bot command this will contain the command, otherwise this will be `None`. If there are additional arguments to the command following the bot command they can be found in `message.bot_command_arguments`.

`message.recieving_room`  If the message is being sent to, or recieved from, a room this will be the name of the room, otherwise this will be `None`.

`message.private_message_recipient`  If the message is a private message, this will be the nick of the user it was being sent to, otherwise this will be `None`.

`message.links`  If the message contains hyperlinks they will be availabe in this property.

`message.bot_command_arguments`  If the message is a bot command this will contain all arguments following the bot command.

### Responding to IRC activity

Once an event is triggered you will want Rafi to do something.  To send a message back to the server you must first construct an `IrcMessage` object.  To construct a new message object as a reply to a recieved message you can use:

    irc_message.new_response_message(the_message_body)

This will construct a new message that is either a PM reply when the recieved message is a PM or a room reply when the recieved message is anything but a PM.  Most of the time this will be sufficent, but if you want more fine grained control over what type of message to create and where or who to send it to you can use these constructor methods in the `IrcMessage` class.

`IrcMessage.new_room_message(the_message_body, off_record = False)`  This will construct a new message to be sent to a room.  You must pass in the body of the message as you want it to appear in the room. You can also specify if you would like the message kept off the record.  Off the record messages will not be logged by Rafi and therefore will not be visible when requesting the room history.

`IrcMessage.new_private_message(the_message_body, a_recieving_nick, off_record = True)`  This will construct a new message to be sent to a specific nick.  You must pass in the body of the message, and the nick you would like to recieve the message.  You can also specify if you would like the message on the record, by default private messages are off the record and therefore not logged.

`IrcMessage.new_server_message(the_message_body, off_record = True)`  This will construct a new message to be sent to the server.  You must pass in the body of the message.  This message is used to send commands like QUIT to the server.  By default server commands are off the record, but you can choose to log it if you would like.

After an `IrcMessage` object is constructed you can send it by returning it from the action function.  You could also send it manually using `irc_bot.send_message(message)` So to construct and send a message to the room you would do something like this:

    message = IrcMessage.new_room_message('My first message')
    IrcBot.shared_instance().send_essage(message)

More examples of the different message types can be found in the `baseModule` module.
