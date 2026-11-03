# Pint Bot
pint_bot is a Discord bot used for tracking debts between users. By default, this is in the form of pints, but you can customise it to whatever you like. It uses an API that stores the debts in a local SQLite database.

## Installation
Install the dev requirements from `dev-requirements.txt`:
```bash
pip install -r dev-requirements.txt
```

### API
1. Run `main.py` to start the API:
```bash
uvicorn api.main:app
```

### Bot
1. Create a new Discord bot in the [Developer Portal](https://discord.com/developers/applications).
2. Invite the bot to your server with the "application.commands" permission.
3. Set up a `.env` file in the bot folder. See the `.env.example` file for reference. Add your Discord Bot Token from the [Developer Portal](https://discord.com/developers/applications) as `BOT_TOKEN` and the API URL as `API_URL`.
4. Customise the settings in the `config.py` file if you wish, or leave them as defaults.
5. Run `pint_bot.py` to start the bot:
```bash
python -m bot.pint_bot
```

## Docker
> **Prerequisites:** [Docker Engine](https://docs.docker.com/engine/) & [Docker Compose](https://docs.docker.com/compose/)
1. Set up a `.env` file in the bot folder. See the `.env.example` file for reference.
2. To build and start both services:
```bash
docker-compose up --build -d
```
3. To verify, run this and you should see two running containers (api healthy, bot up):
```bash
docker-compose ps
```
4. To stop and remove:
```bash
docker-compose down
```

## Usage
- Use `/help` to see all commands.
- Customise the bot using the `.env` files.
- Debts, transactions, and preferences are stored in a local SQLite database.

Both mixed numbers (`2 1/3`) and improper fractions (`7/3`) are supported, as well as decimals.

## Database

By default, the API creates the SQLite database at `api/data/pint_bot.db`. The schema is created automatically on startup. Set the `PINT_BOT_DATABASE_FILE` environment variable to use a different path.

All database access goes through the `DataManager` interface in `api/data_manager.py`. The API endpoints do not contain SQL; `SQLiteDataManager` is the local SQLite implementation.

### Migrating from the JSON files

If you are upgrading an existing installation, import the old `api/data` JSON files into the new database before starting the API:

```bash
python -m api.migrate_json_to_sqlite
```

The migration only runs against an empty database and will refuse to overwrite existing data.

## Testing
Unit tests are written using **pytest**.

### Running the tests
Run all tests from the project root:
```bash
pytest
```

## Customising
- Customise the API by modifying the `config.py` file in the `api` folder (e.g., how much debt to allow per transaction).
- Customise the bot by modifying the `config.py` file in the `bot` folder.
- Customise the way the bot sends messages in the `send_messages.py` file (by default it uses embeds).

## Configuration
- **PINT_BOT_DATABASE_FILE**: Optional path to the local SQLite database (default: `api/data/pint_bot.db`).
- **BOT_NAME**: The name of the bot in Discord.
- **API_URL**: The URL of your API for the economy.
- **CURRENCY_NAME**: The name of the currency used in the economy.
- **CURRENCY_NAME_PLURAL**: The plural name of the currency used in the economy.
- **USE_DECIMAL_OUTPUT**: Set to `True` to use decimal output, or `False` to use fraction output.
- **USE_TABLE_FORMAT_DEFAULT**: Set to `True` to use a table format for output by default (looks good on desktop but doesn't make sense on mobile). Set to `False` for a more mobile-friendly output (recommended).
- **SHOW_PERCENTAGES_DEFAULT**: Set to `True` to show percentages of the total owed by each person or the whole economy in commands that display debts.
- **SHOW_DETAILS_DEFAULT**: Set to `True` to show the full details of debts in commands that display debts.
- **PERCENTAGE_DECIMAL_PLACES**: The number of decimal places to show for percentages if `SHOW_PERCENTAGES_DEFAULT` is `True`.
- **REACT_TO_MESSAGES_MENTIONING_CURRENCY**: Set to `True` to automatically react to messages that mention the name of your currency.
- **REACTION_EMOJI**: The emoji to use when reacting if `REACT_TO_MESSAGES_MENTIONING_CURRENCY` is `True`.
- **REACTION_EMOJI_RARE**: The emoji to use when reacting if `REACT_TO_MESSAGES_MENTIONING_CURRENCY` is `True`.
- **REACTION_ODDS**: The odds of a reaction from occurring if `REACT_TO_MESSAGES_MENTIONING_CURRENCY` is `True`.
- **REACTION_ODDS_RARE**: The odds of the rare reaction from occurring if `REACT_TO_MESSAGES_MENTIONING_CURRENCY` is `True`.
- **TRANSFERABLE_ITEMS**: A list of objects your currency can be transferred into.
- **ECONOMY_HEALTH_MESSAGES**: A list of messages (in descending order) to show when using the `get_all_debts` command, based on the total debts owed in the economy.

## License
MIT Licence