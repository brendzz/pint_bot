# pint_bot

pint_bot is a Discord bot that is used for tracking pint debts between users. It uses an API that stores the debts in JSON file.

## Installation

Install requirements from requirements.txt.
```python
pip install -r requirements.txt
```
### API
1. Run API.py to start the API.
```python
uvicorn API:app
```
### Bot
1. Create new Discord bot in the Developer Portal (https://discord.com/developers/applications)
2. Invite to server with "application.commands" permisions
3. Setup .env file. Add your Discord Bot Token from the Developer Portal as CONST_BOT_TOKEN.
4. Add your API url as CONT_API_URL (if running locally, this is likely "http://127.0.0.1:8000").
5. Run pint_bot.py to start the bot.
## Usage
- /owe [user] [pint_number] [optional: reason] *- Add a pint you own someone else*

Pints are quantised to the nearest 1/6 and each debt can range from 1/6 to 10 pints. Both mixed numbers (2 1/3) and improper fractions (7/3) are supported.
- /pints *- See your own pint debts.*
- /allpints - *- See everyone's pint debts.*
## Customising
- Customise the API my modiying the .env file in the API folder e.g. the currency name, api endpoint names
- Customise the bot by modifying the .env file in the main folder e.g. the 
- Customise the way the bot sends messages in the send_messages.py file (by default it uses embeds)
- To add unicode support - customie fraction_list to add the fractions you need

## Contributing

please don't this is still a work in progress
## License

TBD