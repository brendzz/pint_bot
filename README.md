# Pint Bot
pint_bot is a Discord bot used for tracking debts between users. By default, this is in the form of pints, but you can customise it to whatever you like. It uses an API that stores the debts in a JSON file.

## Architecture
The bot is split into a **platform-agnostic core** and **per-platform adapters**, so other chat platforms (e.g. Telegram) can be added later without touching the economy logic:

- `bot/platform/` — protocols the handlers are written against: `CommandContext`, `PlatformUser`, `Messenger`. No platform SDK imports allowed here (enforced by `tests/test_platform.py`).
- `bot/commands/`, `bot/utilities/` — platform-agnostic command handlers and helpers.
- `bot/platforms/discord/` — the Discord adapter (discord.py): context, embed messenger, slash-command registration, bot setup.
- `bot/platforms/telegram/` — placeholder for a future Telegram adapter. See **Adding a platform** below.
- `bot/pint_bot.py` — entry point; selects the platform via the `PLATFORM` env var (default: `discord`).
- `bot/api_client.py` — async HTTP client for the economy API (shared by all platforms).
- `api/` — the FastAPI economy service (JSON storage with atomic writes + backups).

**Adding a platform:** see `docs/ADDING_A_PLATFORM.md`.

## Security
- The API can require a shared **API key**: set `API_KEY` on the API (environment variable) and the same `API_KEY` in `bot/.env`. The bot sends it as an `X-API-Key` header. `/health` is always open so Docker healthchecks work. If `API_KEY` is unset the API stays open (development default) and logs a warning on startup.
- The dev `docker-compose.yml` binds the API to `127.0.0.1:8000` by default. Only expose it further if you set `API_KEY` (or firewall it). The prod compose uses host networking — set `API_KEY` there too.
- `bot/.env` and `api/data/` are excluded from images via `.dockerignore` — never commit them.

## Data safety
- All JSON data files are written **atomically** (write to temp file, then rename).
- Before every save, the previous file is copied to a `.bak` file. If the main file is corrupt or missing, it is automatically restored from the backup; if neither works the API returns `503 {"detail": "DATA_STORE_UNAVAILABLE"}` instead of crashing.
- Back up `api/data/` (or at least the `.bak` files) regularly.

## API
- Interactive docs: `http://localhost:8000/docs` (Swagger UI) when the API is running.
- `GET /debts` returns `{"users": {"<id>": {"owes": "...", "is_owed": "..."}}, "total_in_circulation": "..."}`.

### API settings (`api/config.py`)
- **MAXIMUM_PER_DEBT**: maximum per individual debt.
- **SMALLEST_UNIT**: smallest fraction allowed (quantization unit).
- **QUANTIZE_OWING_DEBTS** / **QUANTIZE_SETTLING_DEBTS**: enforce quantization for owe/settle.
- **SORT_OWES_FIRST**: ordering used by `GET /debts`.
- **AUTO_REVERSE_EXCESS_CASHOUTS** (default: `False`): when a settle/cashout exceeds the outstanding debt, the excess is converted into a new debt in the **opposite direction** instead of being discarded. Example: Alice owes Bob 1 pint, Bob cashes out 2 pints → Alice's debt is settled, and Bob now owes Alice 1 pint. Applies to API-direct transactions too, not just bot commands. The response includes `auto_reversed_amount`.
- **AUDIT_LOG_ENABLED** (read-only, shown via `GET /settings`): `True` when `AUDIT_LOG_WEBHOOK_URL` is set on the API.

## Audit log (optional, default: off)
Set `AUDIT_LOG_WEBHOOK_URL` on the **API** service to a Discord channel webhook URL and every transaction created through the API — from the bot, curl, scripts, anything — is posted to that channel, including auto-reversed amounts and their direction.

- One message per transaction (`💸 OWE` / `✅ SETTLE`), with amounts, user IDs, reason and timestamp.
- Implemented as a Discord webhook: works even if the bot is offline; the bot is not required in the channel.
- `@everyone` / `@here` in user-supplied reasons are neutralized (`allowed_mentions: parse: []`).
- Webhook delivery failures are logged and never affect the transaction.
- The webhook URL is a secret — set it via environment/CI secrets (`AUDIT_LOG_WEBHOOK_URL`), never in committed config. It is never exposed through `GET /settings`.

With Docker Compose, set it alongside `API_KEY`:
```bash
AUDIT_LOG_WEBHOOK_URL=https://discord.com/api/webhooks/... docker-compose up -d
```

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
5. Run the bot (Discord, by default):
```bash
python -m bot.pint_bot
```
Set `PLATFORM` to choose a different adapter (only `discord` is implemented for now).

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
- Debts are stored in a JSON file.

Both mixed numbers (`2 1/3`) and improper fractions (`7/3`) are supported, as well as decimals.

- **AUTO_REVERSE_EXCESS_CASHOUTS**: (API setting, shown via `/settings`) Auto-convert the excess of an over-limit cashout/settle into a debt in the opposite direction. Default `False`.
- **AUDIT_LOG_ENABLED**: (API setting, shown via `/settings`) Whether an audit-log channel is configured for all transactions. Default off.

## Testing
Unit tests are written using **pytest**. This includes API tests (`tests/test_api.py`, via FastAPI's `TestClient`) and bot-side tests.

### Running the tests
Run all tests from the project root:
```bash
pytest
```

## Customising
- Customise the API by modifying the `config.py` file in the `api` folder (e.g., how much debt to allow per transaction).
- Customise the bot by modifying the `config.py` file in the `bot` folder.
- Customise the way the bot sends messages in the `messenger.py` of your platform adapter (by default Discord uses embeds).

## Configuration
- **BOT_NAME**: The name of the bot in Discord.
- **API_URL**: The URL of your API for the economy.
- **API_KEY**: (Optional) The shared secret the API expects in the `X-API-Key` header. Must match the `API_KEY` set on the API service.
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