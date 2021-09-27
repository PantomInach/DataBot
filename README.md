# DataBot
Discord Bot to track users and other guilde features
## Requirements
You need Python Version 3.6 or newer. Also the requirements musst be installed via `pip3 install -r requirements.txt`.  
## Use Bot
Create a [Discord Application](https://discord.com/developers/applications). Make sure "Presence Intent" and "Server Members Intent" are enabled in Privileged Gateway Intents under the Bot tab. Than copy the token to the specified space in the data/config.json file. Also add your guilde in the "server" space and your Discord in "owner".
Now you need to invite the Bot to your guilde. Use https://discord.com/oauth2/authorize?client_id=INSERT_CLIENT_ID_HERE&scope=bot&permissions=2416143440 after replacing "INSERT_CLIENT_ID_HERE" with your Bots client id under the tab OAuth2.
Than you can run the bot with `python3 main.py` or under Linux with `./startbot.sh`.

