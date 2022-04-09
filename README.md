# DataBot
Discord Bot to track users and other guild features
## Requirements
You need Python Version 3.6 or newer. The requirements must be installed via `pip3 install -r requirements.txt`.  
## Use Bot
Create a [Discord Application](https://discord.com/developers/applications). Make sure "Presence Intent" and "Server Members Intent" are enabled in Privileged Gateway Intents under the Bot tab. Than copy the token to the specified space in the data/config.json file. Also add your guild in the "server" space and your Discord in "owner".
Now you need to invite the Bot to your guild. Use https://discord.com/oauth2/authorize?client_id=INSERT_CLIENT_ID_HERE&scope=bot&permissions=2416143440 after replacing "INSERT_CLIENT_ID_HERE" with your Bots client ID under the tab OAuth2.
Afterwards you can run the bot with `python3 main.py` or on Unix with `./startbot.sh`.