# Pint Bot
pint_bot is a Discord bot used for tracking debts between users. By default, this is in the form of pints, but you can customise it to whatever you like. It uses an API that stores the debts in a JSON file.

## Installation
Install the dev requirements from `dev-requirements.txt`:
```bash
pip install -r dev-requirements.txt
```

### API
1. Set up a `.env` file in the API folder. See the `.env.example` file for reference.
2. Run `api.py` to start the API:
```bash
uvicorn api.main:app
```

### Bot
1. Create a new Discord bot in the [Developer Portal](https://discord.com/developers/applications).
2. Invite the bot to your server with the "application.commands" permission.
3. Set up a `.env` file. See the `.env.example` file for reference. Add your Discord Bot Token from the Developer Portal as `BOT_TOKEN`.
4. Add your API URL to the `config.json` file as `API_URL` (if running locally, this is likely `http://127.0.0.1:8000`). Customise the other settings if you wish, or leave them as defaults.
5. Run `pint_bot.py` to start the bot:
```bash
python -m bot.pint_bot
```

## Usage
- Use `/help` to see all commands.
- Customise the bot using the `.env` files.
- Debts are stored in a JSON file.

Both mixed numbers (`2 1/3`) and improper fractions (`7/3`) are supported, as well as decimals.

## Testing
Unit tests are written using **pytest**.

### Running the tests
Run all tests from the project root:

```bash
pytest
```

## Customising
- Customise the API by modifying the `.env` file in the API folder (e.g., how much debt to allow per transaction, the API endpoint names).
- Customise the bot by modifying the `config.json` file.
- Customise the way the bot sends messages in the `send_messages.py` file (by default it uses embeds).

## config.json
- **BOT_NAME**: The name of the bot in Discord.
- **API_URL**: The URL of your API for the economy.
- **CURRENCY_NAME**: The name of the currency used in the economy.
- **CURRENCY_NAME_PLURAL**: The plural name of the currency used in the economy.
- **USE_DECIMAL_OUTPUT**: Set to `True` to use decimal output, or `False` to use fraction output.
- **USE_TABLE_FORMAT_DEFAULT**: Set to `True` to use a table format for output by default (looks good on desktop but doesn't make sense on mobile). Set to `False` for a more mobile-friendly output (recommended).
- **SHOW_PERCENTAGES_DEFAULT**: Set to `True` to show percentages of the total owed by each person or the whole economy in commands that display debts.
- **PERCENTAGE_DECIMAL_PLACES**: The number of decimal places to show for percentages if `SHOW_PERCENTAGES_DEFAULT` is `True`.
- **REACT_TO_MESSAGES_MENTIONING_CURRENCY**: Set to `True` to automatically react to messages that mention the name of your currency.
- **REACTION_EMOJI**: The emoji to use when reacting if `REACT_TO_MESSAGES_MENTIONING_CURRENCY` is `True`.
- **TRANSFERABLE_ITEMS**: A list of objects your currency can be transferred into.
- **ECONOMY_HEALTH_MESSAGES**: A list of messages (in descending order) to show when using the `get_all_debts` command, based on the total debts owed in the economy.

## License
MIT Licence