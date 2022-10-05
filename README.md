# DataBot
Want to track to time your members spend on your Discord server?
Then look no further.
With this Discord bot, you can track the talking time including the send messages with an included leveling system.
To see the users stat's, the bot provides an interactive leader board, in which you can sort by different aspects.
Also, the bot provides many other features, to handle many aspects for your server from giving roles via reactions to making polls.
With the unique subserver feature of the bot, there is no need to split up the server into many other smaller ones.
Instead, create a subserver to create individual spaces for many parts of your community, so that there can exist shielded from others parts of your server.

## Features
### Leveling system
- Track the users time in voice channel.
- Track how many messages a user send.
- Channels are configurable if they should track the voice time or messages.
- Interactive leader board to view your level and stats.
- Levelcards for individual users.
### Polls
- Create polls in the dm with the bot and have a live view of the polls look.
- Open your poll on your server to enabled users to vote on a topic via reactions. All anonymous.
- Publish the results of a poll.
- Possablity to edit the poll every time if any mistake happened.
### Tables
- Create a table for users to get roles via reactions.
- Configure the table in the configs and post it into a channel.
- Update the table without any lose of reactions.
### Subserver
- Easily create private parts of your server with subserver.
- Invite people to subserver or create an invitecode.
- Switch to a subserver by joining a gateway channel or over a bot command.
### Other stuff
- Make voice channel dynamically expand by simply adding '#1' on its name.
- Get inspirational quotes from 'inspirobot.me'.
- Many command tools to manage the bot.

## Requirements
You need Python Version 3.6 or newer. 
The requirements must be installed via `pip3 install -r requirements.txt`.  
That's it.

## Installation
Run `git clone https://github.com/PantomInach/DataBot.git` in your installation folder or download the repository manually.

## Create a bot
Create a [Discord Application](https://discord.com/developers/applications) on the site [https://discord.com/developers/applications](https://discord.com/developers/applications).
Make sure "Presence Intent" and "Server Members Intent" are enabled in Privileged Gateway Intents under the Bot tab.
Then copy the token to the specified space in the data/config.json file.
More to the config file in [Configuration](#Configuration).
Also add your guild in the "server" space and your Discord ID in "owner".
Now you need to invite the Bot to your guild.
Use https://discord.com/oauth2/authorize?client_id=INSERT_CLIENT_ID_HERE&scope=bot&permissions=2416143440 after replacing "INSERT_CLIENT_ID_HERE" with your Bots client ID under the tab OAuth2.
The bot is now created and invited to your server.

## Configuration
### Bot config
The main config file can be found here [config](https://github.com/PantomInach/DataBot/blob/main/data/config.json) in the directory [data](https://github.com/PantomInach/DataBot/blob/main/data).
```
{
      "token": "Your token",
      "command_prefix": "+",
      "log": "False",
      "logchannel": "",
      "levelchannel": "",
      "owner": "",
      "textCooldown": "75",
      "privilege": {
            "Your ID": "2",
            "Lower rank ID": "1"
      },
      "guild": "Your guild ID",
      "serverVoiceBlacklist": [
            "0"
      ],
      "serverTextWhitelist": [
            "0"
      ],
      "roles": [],
      "rolesXPNeed": [],
      "needForSubServer": []
}
```
- `token` contains your token from the step [Create a bot](#create_a_bot)
- `command_prefix` is the symbol one, which the bot listens. If the prefix is `+`, then you can invoke a command via `+help` for example.
- `log` describes if the bot should track your users voice time and sent messages. Can be set with a command.
- `logchannel` is a channel, in which the bot sends welcome and goodbye messages.
- `levelchannel` is a channel for the leveling related stuff.
- `owner` should contain your discord id.
- `textCooldown` describes how long a new message of a user doesn't give him exp, when he already got exp from an earlier message.
- `privilege` describes the bot intern permissions hierarchy.
   - Enter an discord id and then the level.
   - The higher the level the more permissions a user gets when interacting with the bot.
   - Level `1` are moderator and Level `2` are admins.
- `guild` should contains the discord server id, on which the bot should run.
- `serverVoiceBlacklist` contains all voice channel, where the user time should not be collected. Channel can be added via commands or by hand.
- `serverTextWhitelist` contains all text channel, where the users send messages should be collected. Channel can be added via commands or by hand.
- `roles` contains the roles, which the bot should give a user, when he reached a level specified in `rolesXPNeed`. The order of the roles is important.
- `needForSubServer` contains any role a user needs to use subserver. Only one role is needed.

### Command config
The command config is for specifying what command should work in which text channel or be invokable by which user with certain roles.
The config file [commandRights.json](https://github.com/PantomInach/DataBot/blob/main/data/commandRights.json) can be found in the directory [data](https://github.com/PantomInach/DataBot/blob/main/data).
An entry contains the following:
```
"command name":
  {
    "roles":[
      "roles which are required",
      "id or name"
    ],
    "channel":[
      "in which channel is the command invokable",
      "id or name"
    ]
  } 
```
