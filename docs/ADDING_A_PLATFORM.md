# Adding a Chat Platform (e.g. Telegram)

The bot is split into a **platform-agnostic core** and **per-platform adapters**.
Telegram support is *not* implemented — this document is the contract for it.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Platform-agnostic core (no chat-platform SDK imports)       │
│                                                             │
│  bot/platform/        Protocols: CommandContext, PlatformUser, Messenger │
│  bot/commands/        Command handlers (owe, settle, help, …) │
│  bot/utilities/       Pure helpers (formatter, chunking, …)   │
│  bot/api_client.py    HTTP client for the economy API        │
│  bot/setup/           Command registry + API settings sync   │
│  models/              Shared pydantic models                 │
└─────────────────────────────────────────────────────────────┘
                ▲                              ▲
┌───────────────┴───────────┐   ┌──────────────┴────────────┐
│  Discord adapter          │   │  Telegram adapter         │
│  bot/platforms/discord/   │   │  bot/platforms/telegram/  │
│  (implemented)            │   │  (to be implemented)      │
└───────────────────────────┘   └───────────────────────────┘
```

Enforcement: `tests/test_platform.py` fails the build if any shared-layer
module imports a chat-platform SDK.

### The contract

Handlers receive a `CommandContext` and know nothing else about the platform:

```python
class CommandContext(Protocol):
    user_id: str                # invoking user, as a string
    user_display_name: str
    user_mention: str           # platform-native mention markup
    bot_user_id: str            # the bot's own user id (for "can't owe the bot")
    raw: Any                    # escape hatch: Interaction / Update / …
    messenger: Messenger        # how replies are sent

    async def defer(self) -> None: ...
    async def display_name(self, user_id: str, *, force_refresh: bool = False) -> str: ...
```

Outgoing messages go through the `Messenger` protocol:

```python
class Messenger(Protocol):
    async def info(self, ctx, *, title: str, description: str) -> None: ...
    async def success(self, ctx, *, title: str, description: str) -> None: ...
    async def error(self, ctx, *, title: str, description: str) -> None: ...
    async def one_column_table(self, ctx, *, title, description, data, table_format) -> None: ...
    async def two_column_table(self, ctx, *, title, description, data, table_format) -> None: ...
```

`data` rows for the tables are unchanged: dicts with `Setting`/`Value` keys
(one-column) and `name`/`Owes`/`Is Owed` keys (two-column).

## Checklist: implementing the Telegram adapter

1. **Dependency** — add your framework of choice to `bot/requirements.txt`.
   [aiogram 3.x](https://docs.aiogram.dev/) is recommended; `python-telegram-bot` works too.
   Do not remove discord.py; the same repo serves both.

2. **Layout** — create `bot/platforms/telegram/` with:
   - `__init__.py`
   - `context.py` — `TelegramCommandContext` implementing `CommandContext`
   - `messenger.py` — `TelegramMessenger` implementing `Messenger`
   - `register_commands.py` — command handlers registration (the Telegram equivalent of slash commands)
   - `bot.py` — entry/startup (connect, register commands via `BotCommand`s, run)

3. **`TelegramCommandContext`**
   - `user_id = str(message.from_user.id)`, `user_display_name = message.from_user.full_name`.
   - `user_mention`: e.g. `f'<a href="tg://user?id={id}">{name}</a>'` (HTML parse mode) or `@username`.
   - `bot_user_id`: `(await bot.me()).id` once at startup, cached on the context or a module constant.
   - `raw`: the Telegram `Message`/`Update`.
   - `defer()`: Telegram has no interaction/defer cycle. Either send a placeholder
     ("⏳ Working…") and later `edit_message_text`, or make `defer()` a no-op and just reply —
     acceptable for an economy bot with a fast API. `callback_query`s (if you add buttons)
     should use `answer()` to stop the loading spinner.
   - `display_name()`: `bot.get_chat(user_id)` → `full_name`. Note Telegram can only
     resolve chats the bot knows about (e.g. users who messaged it); on error or
     `None`, fall back to the shared resolver in `bot/utilities/display_names.py`
     (returns `"Unknown User (<id>)"`). Reuse `resolve_display_name()` for the
     built-in TTL cache.

4. **`TelegramMessenger`** — semantic levels map to styling, e.g. with HTML parse mode:
   - `info` → `ℹ️`, `success` → `✅`, `error` → `❌` prefix/title
   - titles as `<b>…</b>` first line; descriptions as body
   - **Message length limit is 4096 chars** — reuse
     `bot.utilities.message_processor.split_text_into_chunks`; send multiple messages.
   - **Tables**: no embed fields. Render `table_format=True` as a monospace
     `<pre>` block with aligned columns; `table_format=False` as one block per row.
   - Titles are truncated to something sensible (`<b>`…`</b>` counts toward the limit).

5. **Registering commands** — Telegram bots use `/` commands
   (`/owe 2 1/3 Beer money`). Two viable routes:
   - **aiogram routers**: one `Router`, a `Command` filter per command, and
     `message.from_user` → build `TelegramCommandContext(message)`.
   - **Bot API `setMyCommands`**: advertise `/help`, `/pints`, … in the menu.
   Handler signatures map 1:1 onto the existing handlers — they take `ctx` +
   typed arguments, so no handler changes should be needed. Parse arguments
   with `aiogram`'s filters or a small manual parser (amounts may contain
   spaces: `2 1/3`, so prefer “rest of string” capture, then `shlex`-style split).

6. **Dispatch** — add `"telegram"` to `SUPPORTED_PLATFORMS` in `bot/pint_bot.py`
   and a branch importing `bot.platforms.telegram.bot.main`. Keep the import lazy.

7. **Configuration**
   - Add `TELEGRAM_BOT_TOKEN` (and optionally `TELEGRAM_API_ID/HASH`) to `bot/.env.example`
     with documentation. Discord uses `BOT_TOKEN`; do not overload it.
   - `bot/config.py` stays shared — currency, decimals, economy messages are platform-neutral.
     Put Telegram-only knobs (e.g. parse mode) in the Telegram adapter, not in shared config.

8. **Deployment** — one image, env-selected platform. Add to `docker-compose.yml`
   a second bot service (or a profile) running the Telegram adapter with `PLATFORM=telegram`,
   or a separate service definition `bot-telegram`. CI builds one image per platform
   only if dependencies diverge (they will, once aiogram is added — the Discord
   flavour doesn't need it). Consider two Dockerfiles:
   `bot/Dockerfile.discord` and `bot/Dockerfile.telegram`, or a build-arg.

9. **Tests** — mirror `tests/conftest.py`:
   - A `DummyTelegramMessage`/`DummyTelegramContext` pair with the same shape as the
     Discord doubles (`raw`, `user_id`, `defer()`, …).
   - A `RecordingTelegramMessenger` (or assert on `sendHTML` calls) mirroring
     `RecordingMessenger`.
   - The generic tests (`test_platform.py`) keep passing as-is — extend
     `test_discord_adapter_satisfies_protocols` with a Telegram equivalent.

## Known rough edges to plan for

- **Markup is Discord-flavoured.** Handlers emit text containing `**bold**` and
  `__underline__` (Discord markdown). For Telegram either (a) translate that subset
  in `TelegramMessenger` (`**…**` → `<b>…</b>`, `__…__` → `<u>…</u>`), or (b) replace
  these tokens in the shared formatter with platform-neutral markers and render per
  adapter. Option (a) is pragmatic; option (b) is cleaner if more platforms arrive.
- **No embeds on Telegram** — long tables (e.g. `/all_pints`) may need paging like
  the Discord `(Page N/M)` handling; keep `split_text_into_chunks` and chunk at
  message boundaries instead of embed boundaries.
- **No interactions/defers** — see `defer()` above.
- **Permissions** — Telegram bots can't read arbitrary users' display names; expect
  `"Unknown User (<id>)"` for users who never messaged the bot, and prefer storing
  names on first contact if that matters to you.
- **Rate limits** — ~30 msg/s global, 1 msg/s per chat; the messenger should
  tolerate a "message not modified" / "retry after" error gracefully.

## What stays untouched

Everything in the shared core: `api_client` (async already), the economy API,
pydantic models, fraction handling, debt formatters, error codes/messages, the
command registry, and the test suite's FakeAPI fixtures. If you find yourself
editing those files to add Telegram, the adapter boundary has been breached —
stop and reconsider.
