# pint_bot

pint_bot is a Discord bot that is used for tracking debts between users. By default, this is in the form of pints, but you can customise it to whatever you like. It uses an API that stores the debts in JSON file.

## Installation

Install requirements from requirements.txt.
```python
pip install -r requirements.txt
```
### API
1. Setup a .env file in the API folder. See the .env.example.
2. Run API.py to start the API.
```python
uvicorn API:app
```
### Bot
1. Create new Discord bot in the Developer Portal (https://discord.com/developers/applications)
2. Invite to server with "application.commands" permisions
3. Setup .env file. See the .env.example. Add your Discord Bot Token from the Developer Portal as BOT_TOKEN and the name you want the to bot to use as BOT_NAME.
4. Add your API url as API_URL (if running locally, this is likely "http://127.0.0.1:8000").
5. Run pint_bot.py to start the bot.
## Usage
- /help - to see all commands
- Customise the bot using the .env files

Both mixed numbers (2 1/3) and improper fractions (7/3) are supported, as are decimals.

## Customising
- Customise the API my modiying the .env file in the API folder e.g. how much debt to allow per transaction, the api endpoint names
- Customise the bot by modifying the .env file in the main folder e.g. the currency name
- Customise the way the bot sends messages in the send_messages.py file (by default it uses embeds)

## License
MIT Licence