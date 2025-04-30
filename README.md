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
3. Setup .env file. See the .env.example. Add your Discord Bot Token from the Developer Portal as BOT_TOKEN.
4. Add your API url to the Config/bot_config.json file as API_URL (if running locally, this is likely "http://127.0.0.1:8000"). Customise the other settings if you wish or leave as defaults.
5. Run pint_bot.py to start the bot.
## Usage
- /help - to see all commands
- Customise the bot using the .env files
- Debts are stored in a json file

Both mixed numbers (2 1/3) and improper fractions (7/3) are supported, as are decimals.

## Customising
- Customise the API my modiying the .env file in the API folder e.g. how much debt to allow per transaction, the api endpoint names
- Customise the bot by modifying the bot_config file in the main folder e.g. the currency name
- Customise the way the bot sends messages in the send_messages.py file (by default it uses embeds)

## bot_config.json
BOT_NAME = Name of the bot in Discord
API_URL = The URL of your API for the economy
CURRENCY_NAME = The name of the currency used in the economy
CURRENCY_NAME_PLURAL = Plural name of the currency used in the economy
USE_DECIMAL_OUTPUT = True to use decimal output, False to use fraction output
USE_TABLE_FORMAT_DEFAULT = True to set the default for output on certain commands to use a table format that looks good on desktop but doesn't make sense on mobile, False to use a more mobile friendly output by default (recommended)
SHOW_PERCENTAGES_DEFAULT = True to set the default for commands showing pint debts to also show what percetanges of the total owed by that person/the whole economy each debt is
PERCENTAGE_DECIMAL_PLACES = The number of decimal places to show the above percetanges to if it is True
REACT_TO_MESSAGES_MENTIONING_CURRENCY = True to automatically react to messages that contain the name of your currency.
REACTION_EMOJI = The emoji to use when reacting.
TRANSFERABLE_ITEMS = The list of objects your currency can be transfered into
ECONOMY_HEALTH_MESSAGES = In descending order, a list of what messages to show when using the get_all_debts command based on how many debts are owed in the total economy.

## License
MIT Licence