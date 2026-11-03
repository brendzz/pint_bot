# Pint Bot — Fix Report

Date: 2026-11-03 · Scope: bugs, security, robustness, CI/CD, tests, docs.
All **118 tests pass** (85 pre-existing + 33 new API tests). Live smoke test passed: `/health` open, auth enforced (401 without/with wrong `X-API-Key`, 200 with correct key).

---

## 1. Bugs fixed

### 1.1 `/transactions` command crashed when `user_id` was provided 🔴
- **Root cause:** `bot/setup/register_commands.py` passed the command's `user_id: str` into `handle_get_transactions(...)`, whose 4th parameter was declared `user: discord.User`. The handler then did `str(user.id)` → `AttributeError`, silently killing the command (interaction had already been deferred).
- **Fix:** handler signature is now `user_id: Optional[str] = None` (`bot/commands/debt_display.py`); the value is used directly (stripped, empty → `None`). The parameter order matches the command callback, so no caller changes needed.
- **Bonus fix in the same function:** empty transaction lists were unreachable (`if not data` never fired because the API always returns a truthy dict). Now `transactions` is extracted with `data.get(...)` and an empty list shows "No Transactions Found".
- **Bonus:** `display_as_settle` default aligned with config (was `True`, ignored anyway).

### 1.2 Mixed-number fraction parser accepted malformed input 🔴
- **Root cause:** `api/fraction_functions.py` split on spaces/slashes and `int()`-parsed parts without any validation.
  - `"3 -1/2"` → `5/2` (silently wrong)
  - `"2 7/3"` → `13/3` (improper fraction in a mixed number)
  - `"-2 1/2"` → `-3/2` (wrong sign handling)
  - `"1_000"` → `1000` (Python allows underscores in int literals)
- **Fix:** regex-driven parser with three strict grammars: plain number (`^-?(\d+(\.\d+)?|\.\d+)$`), simple fraction (`^(-?)(\d+)/(\d+)$`, improper allowed), mixed number (`^(-?)(\d+)\s+(\d+)/(\d+)$`, fractional part must be a *proper* fraction). Anything else → `400 INVALID_AMOUNT`. A leading `-` now negates the whole mixed number correctly (`-2 1/2` → `-5/2`, still rejected downstream as negative).
- **Tests:** parametrized cases added in `tests/test_api.py` (plus existing `test_fraction_functions.py` still passes).

### 1.3 Over-long embed titles crashed the send 🔴
- **Root cause:** `check_title_length()` in `bot/utilities/message_processor.py` sent an error message and then **fell through** to send the original embed anyway → Discord HTTP 400 → exception propagated out of the command.
- **Fix:** replaced with `truncate_title()` — titles longer than `DISCORD_EMBED_TITLE_LIMIT` (256) are truncated with an ellipsis and the message is always sent. Simpler, no double-send, no exception.

### 1.4 Unicode-preference failure double-messaged the user 🔴
- **Root cause:** `fetch_unicode_preference()` caught API errors, sent an error embed, **and** returned `False`, so the calling command continued and sent a second (success) embed.
- **Fix:** on failure it logs a warning and silently falls back to `False` (the preference is cosmetic). No more contradictory double messages.

### 1.5 Config drift between settings and models 🔴
- **Root cause:**
  - `DebtEntry` hardcoded `Field(le=10)` while `MAXIMUM_PER_DEBT` lives in `api/config.py` — raising the config broke debt creation.
  - `MAXIMUM_DEBT_CHARACTER_LIMIT` was read from an **env var nothing sets** in three model files, while `api/config.py` had its own hardcoded `200` — editing the config had no effect.
- **Fix:**
  - New shared module `models/limits.py` owns `MAXIMUM_DEBT_CHARACTER_LIMIT` (env-overridable); models and `api/config.py` import it — single source of truth.
  - `DebtEntry` now only enforces `gt=0`; the upper bound is enforced once, at the API layer (`check_in_range` with `MAXIMUM_PER_DEBT`).
  - `OweRequest`/`SettleRequest` now require `debtor`/`creditor > 0` (negative Discord IDs rejected with 422).
- **Dead code removed:** `models/user_data.py` (`UserData`, unused), `api/config.py`'s unused `DATA_FILE`/`BASE`.

### 1.6 Avatar-less bot crashed on mention 🔴
- **Root cause:** `bot/pint_bot.py` called `bot.user.avatar.url`; `avatar` is `Optional` and `None` for bots without a custom avatar → `AttributeError`.
- **Fix:** thumbnail is only set when `bot.user.avatar` is truthy. Also converted prints to `logging`.

### 1.7 Invalid user-supplied dates produced 500s 🔴
- **Root cause:** `sanitize_dates()` returned the literal string `"Invalid date"` for unparseable input, which `isoparse()` in the API then choked on → unhandled exception.
- **Fix:** `sanitize_dates()` now parses strictly and raises `ValueError`; `handle_get_transactions` catches it and replies with a friendly `INVALID_DATE` error (new error message added to `bot/utilities/error_messages.py`). Also fixed `to_percentage()` division-by-zero (returns `(0.0%)` instead of raising) and `with_emoji_visuals()` rounding (round-half-up, never negative emojis).

### 1.8 Corrupt JSON data file = permanently broken API (no backup) 🔴
- **Root cause:** `api/data_manager.py` did `json.loads(file.read_text())` with no recovery, and `write_text()` was non-atomic — a crash mid-write would destroy the economy ledger.
- **Fix (`api/data_manager.py` rewritten):**
  - **Atomic writes:** write to `<file>.tmp`, then `os.replace()` onto the target.
  - **Automatic backup:** previous contents copied to `<file>.bak` before every save.
  - **Self-healing load:** corrupt/missing main file → restore from `.bak` (logged); unrecoverable → raises `DataStoreError`.
  - API maps `DataStoreError` → **503 `{"detail": "DATA_STORE_UNAVAILABLE"}`** (global exception handler); unexpected errors → **500 `{"detail": "INTERNAL_ERROR"}`** — never a stack trace to the client.
- **Test:** `tests/test_api.py::TestDataManagerResilience` covers backup creation, auto-restore after corruption, and 503 behaviour.

### 1.9 Debt added, then crash before confirmation 🟠
- **Root cause:** `handle_owe()` called `api_client.debts_with_user(...)` outside any try block; if it failed, the user got no confirmation even though the debt *was* recorded.
- **Fix:** the running-total lookup is now best-effort — on failure it logs a warning and omits the "New Total" line; the success confirmation is always sent.

### 1.10 Misc correctness
- `to_percentage(1, 0, …)` → `(0.0%)` instead of `ZeroDivisionError` (test updated to the new contract).
- `with_emoji_visuals()` uses round-half-up and clamps at 0 emojis.
- `utils`: `_user_display_name_cache` now has a **10-minute TTL** and a **1000-entry cap** (oldest evicted); `fetch_user` HTTP/parse errors degrade to "Unknown User" instead of raising.
- `send_messages`: page indicator `(Page 1/N)` only shown when there is more than one page.
- `debt_helpers.current_timestamp()` now returns ISO-8601 UTC (`%Y-%m-%dT%H:%M:%SZ`), matching transaction timestamps; it was naive **local** time in an ambiguous `%d-%m-%Y` format. Old entries still parse (bot uses `dayfirst=True`).
- `add_debt` returns the **same** timestamp that was stored on the entry (was two separate `now()` calls).
- Dead duplicated `result = {}` initialisation in `/debts` removed.

---

## 2. Security fixes

### 2.1 API had zero authentication and compose exposed port 8000 publicly 🔴
- **Fix:** optional shared-secret auth (`api/auth.py`):
  - Set `API_KEY` on the API → every endpoint except `/health` requires the `X-API-Key` header (constant-time comparison, `401 INVALID_API_KEY` otherwise).
  - Unset → open access (dev default) with a startup warning logged — nothing breaks on upgrade.
  - Bot sends the header automatically when `API_KEY` is in `bot/.env` (`bot/api_client.py`, `bot/config.py`, `bot/.env.example` updated).
  - Dev `docker-compose.yml` now binds `127.0.0.1:8000:8000`; prod keeps host networking but documents `API_KEY`.
- **Verified live:** uvicorn boot → `/health` 200, `/debts` 401 (no key), 401 (wrong key), 200 (correct key).

### 2.2 `.dockerignore` leaked secrets and data into images 🔴
- **Root cause:** `COPY bot /app/bot` would bake `bot/.env` (BOT_TOKEN) and `COPY api /app/api` would bake `api/data/*.json` (real user IDs + balances) into images — publishable to GHCR.
- **Fix:** `.dockerignore` now excludes `*.env`, `**/.env*`, `data/`, `api/data/`, `.git`, `.github`, `tests/`, `.venv`, caches, OS/editor files.

### 2.3 Deploy workflow destroyed unrelated host resources 🔴
- **Root cause (`.github/workflows/deploy.yml`):** `lsof -ti:8000 | xargs kill -9` (killed *any* process on :8000), `podman ps -a -q | xargs podman rm -f` (**deleted every container on the host**), `systemctl --user stop/disable podman*` (killed unrelated user services), `podman pod rm -f` for all pods, stale-CNI-lock deletion, and `timeout-minutes: 1` (too short for the script).
- **Fix:** destructive, host-wide operations **removed**; shutdown is limited to `podman-compose -f docker-compose.prod.yml down` (this project only). `timeout-minutes: 15`. Deploy also writes `API_KEY` (new optional `PROD_API_KEY` secret) into `bot/.env` and exports it for the API container. CI `test.yml`: unnecessary `packages: write` permission dropped, concurrency group fixed.
- **Note:** removing pre-existing containers from *before* this fix on the prod host is out of scope — if the old deploy globbed and deleted shared containers, that history can't be undone; the new script never does it.

### 2.4 Duplicate Discord libraries 🟠
- `requirements`/`dev-requirements` installed both `discord.py==2.5.2` and `py-cord==2.6.1`, which install the **same** `discord/` package tree; whichever installed last silently won (they overwrote each other — the dev venv was actually broken after uninstall proved this).
- **Fix:** py-cord removed; discord.py 2.5.2 force-reinstalled; full suite passes. Docker images were never affected at runtime install order, but the conflict was a landmine.

### 2.5 Logging hygiene 🟡
- `logging.basicConfig(level=logging.DEBUG)` → `INFO`; bot uses `logger` instead of bare `print`; API logs data-store failures and unhandled exceptions (stack traces go to logs, not clients).

---

## 3. Robustness / design improvements

### 3.1 Sync `requests` blocked the Discord event loop 🟠
- **Fix:** `bot/api_client.py` rewritten — all calls are `async` and run the blocking I/O in a worker thread via `asyncio.to_thread` (no event-loop stalls, no new dependency). All ~13 call sites updated to `await`; test fakes (`tests/conftest.py`) updated to `async def` accordingly.
- Rejected alternative: swapping to `httpx`/`aiohttp` — unnecessary dependency churn for the same effect; can be revisited later.

### 3.2 `on_ready` re-registered and re-synced all commands on every reconnect 🟠
- **Fix:** module-level `_commands_registered` flag — commands register and `tree.sync()` runs once per process; reconnects just log. (Native `setup_hook()` would be the next step if the bot grows subclasses.)

### 3.3 `GET /debts` returned a polymorphic object 🟡
- **Fix:** response is now `{"users": {<id>: {"owes", "is_owed"}}, "total_in_circulation": "<fraction>"}`. Bot updated (`if not users: → NO_DEBTS_IN_ECONOMY`); the bot's exact-dict-match hack (`== {'total_in_circulation': '0'}`) is gone. Test fixture updated.
- **Bot/API must be deployed together** (they are, via compose) since the schema changed.

### 3.4 Error-code plumbing 🟡
- API returned human-readable English in `detail` that the bot then reverse-engineered with `split(":")`. Now the API returns stable codes (`INVALID_TRANSACTION_TYPE`, etc.); the bot maps codes → `ERROR_MESSAGES`, with a correct fallback key (`UNKNOWN_API_ERROR` → `UNKNOWN_API_ERROR_FORMAT` bug fixed — the referenced key didn't exist).

### 3.5 Typing & validation consistency 🟡
- Discord command params annotated `bool/str/User = None` → `Optional[bool/str/User]` (discord.py treats these properly, avoids runtime surprises).
- Discord IDs validated `gt=0` in request models.

---

## 4. Infrastructure, CI/CD, Docker

- **`api/Dockerfile`:** added `HEALTHCHECK` (`curl -fsS …/health`, 30s interval).
- **`docker-compose.yml` (dev):** API bound to localhost; healthcheck for API; bot `depends_on: api: condition: service_healthy`; `API_KEY` passthrough via env.
- **`docker-compose.prod.yml`:** API healthcheck; bot waits for healthy API; `API_KEY` passthrough; comment documenting that host networking must be firewalled or `API_KEY` set (container runs as uid 1000 — `./api/data` must be writable by uid 1000: `chown -R 1000:1000 api/data`).
- Both compose files validated with `docker compose config`.

---

## 5. Tests

- **New:** `tests/test_api.py` — 33 tests over a temporary data dir (FastAPI `TestClient`): health/open access, 401 auth matrix, owe/settle flows (incl. partial settle, settle-more-than-owed, NONE_DEBTS_FOUND), amount parser edge cases, transaction recording & filtering (`type=owe|settle|cashout`, `user_id`), invalid type/date-range handling, preference round-trip, settings shape, **backup/restore of corrupt data files** (503 without backup).
- **Changed:** `tests/conftest.py` (async FakeAPI), `tests/test_debt_display.py` (new `/debts` schema), `tests/test_formatter.py` (zero-division now returns 0.0% by design).
- `httpx` added to `dev-requirements.txt` (required by TestClient).
- **Result: 118 passed** (was 85).

---

## 6. Documentation & housekeeping

- `README.md`: new **Security** (API_KEY, localhost binding, image contents) and **Data safety** (atomic writes, `.bak` auto-restore, 503 semantics, backup advice) sections; `/debts` schema documented; testing section mentions API tests; installation unchanged.
- `bot/.env.example`: documented `API_KEY`.
- `dev-requirements.txt`: py-cord removed, httpx added. `bot/requirements.txt`: py-cord removed.

---

## 7. Deliberately NOT done (recommendations)

1. **JSON storage → SQLite/Postgres.** The file store with atomic writes + backups is now safe against crashes, but it doesn't scale to high concurrency or unbounded transaction history (full re-read per `/transactions` call). Migrate when the economy outgrows a single host.
2. **`/transactions` pagination** — the endpoint returns everything in range; add `limit`/`offset` when history grows.
3. **IDs as strings** (`OweRequest.debtor: str` + snowflake regex) instead of `int` — JSON clients above 2⁵³ lose precision; Python/Discord are fine today, but it's a latent hazard for any external consumer.
4. **Native `Bot.setup_hook()`** for command registration instead of the `_commands_registered` flag.
5. **Root `./data/` directory** (legacy duplicate of `api/data/`, contains real user IDs) is untracked but still on disk — delete it manually once you've confirmed nothing references it (nothing does; the API uses `api/data/`).
6. **Request rate limiting** on the API — not needed while it's a private backend; add if exposed publicly.
7. **Backup retention/off-site copies** of `api/data/*.bak` — automate (e.g. nightly cron) for real disaster recovery.
8. **Provision `PROD_API_KEY`, `PROD_BOT_TOKEN`, `PROD_API_URL`** in GitHub secrets before the next prod deploy; until then the API stays open (with a warning) exactly as before.

## 8. Deployment notes

- Bot and API both changed; deploy them together (compose handles this).
- No data migration required — existing `debts.json`/`transactions.json`/`preferences.json` load as before. Old debt timestamps (`DD-MM-YYYY`) are still displayed correctly; new entries use ISO-8601 UTC.
- First save after deploy creates `.bak` files next to the data files — make sure the mounted `api/data` dir is writable by uid 1000.

---

## 9. Multi-platform architecture (Discord today, Telegram-ready)

The bot was restructured so a second chat platform can be added without touching the economy logic:

- **New shared contracts** (`bot/platform/`): `CommandContext` / `PlatformUser` protocols (what a handler may know about the invoking user and chat) and `Messenger` (semantic `info` / `success` / `error` / `one_column_table` / `two_column_table` sends). No SDK imports allowed here.
- **Handlers** (`bot/commands/`), **pure helpers** (`bot/utilities/`), and the **async API client** are now platform-agnostic — verified by `tests/test_platform.py`, which also enforces the layering in CI.
- **Discord adapter** (`bot/platforms/discord/`): `DiscordCommandContext`, `DiscordMessenger` (embeds, title truncation, chunk splitting), `register_commands.py` (moved from `bot/setup/`), and `bot.py` (Bot + events + `main()`).
- **Entry point** `bot/pint_bot.py` is now a dispatcher: `PLATFORM=discord` (default) launches Discord; unknown values exit with a clear message; `bot/platforms/telegram/` is a documented placeholder.
- Deleted `bot/utilities/send_messages.py` and `bot/utilities/user_utils.py` (logic absorbed into the adapter and `bot/utilities/display_names.py`, a shared TTL-cached name resolver).
- Test doubles (`tests/conftest.py`) now record through the `Messenger` protocol; the suite exercises the real `DiscordCommandContext` adapter in every command test.
- **Not implemented:** Telegram itself. See `docs/ADDING_A_PLATFORM.md` for the full adapter contract and walkthrough (Checklist: context, messenger with `<pre>` tables, `setMyCommands` registration, `TELEGRAM_BOT_TOKEN`, dispatcher branch, deployment profile, test doubles) and known rough edges (Discord-flavoured markup, no defer cycle, 4096-char limit, getChat limits).
- Result: **124 tests pass** (5 new architecture/platform tests).

---

## 10. Features: auto-reverse excess cashouts + transaction audit log

Two new capabilities, both enforced at the API layer so they apply to the bot **and** any direct API client (curl, scripts):

### 10.1 AUTO_REVERSE_EXCESS_CASHOUTS (default: off)
- **api/config.py**: new `AUTO_REVERSE_EXCESS_CASHOUTS: bool = False`.
- **api/main.py `settle_debt`**: when the settled amount is below the requested amount, the excess no longer vanishes. If the setting is on, a DebtEntry in the **opposite** direction is created (e.g. Alice owes Bob 1 pint, Bob cashes out 2 → Alice's debt settled, Bob now owes Alice 1 pint), persisted in the same all-or-nothing `save_debts()` write, and recorded as an `owe` transaction.
- Applies only when a settled debt *relationship exists* (the `NO_DEBTS_FOUND` guard is unchanged — the setting does not conjure debt out of thin air).
- Response now includes `auto_reversed_amount` (bot uses it to display one extra line: *"…now owes you X (excess auto-reversed)"* in settle and *"You now owe … (excess auto-reversed)"* in cashout).
- Bot: `bot/config.py` default, synced from `GET /settings` on startup (`bot/setup/update_settings_from_api.py`), shown in `/settings` ("Auto-reverse Excess Cashouts").

### 10.2 Audit log channel (default: off)
- **api/audit.py**: `record_transaction()` posts one message per transaction (💸 OWE / ✅ SETTLE) to the Discord webhook in `AUDIT_LOG_WEBHOOK_URL`. Works from any client, even if the bot is offline (it's a webhook, not the bot). `allowed_mentions: {parse: []}` neutralises `@everyone`/`@here` in reasons; USER IDs are shown as plain text.
- Hooked into `add_debt`, `settle_debt`, and the auto-reverse path — including API-direct writes.
- Webhook failures are logged and never affect the transaction (tested).
- `AUDIT_LOG_ENABLED` (derived from the env var, never the URL itself) is exposed via `GET /settings` and the bot's `/settings` ("Transactions Posted to Audit Channel"). Webhook URL itself is a secret — env/CI only.
- Both compose files pass `AUDIT_LOG_WEBHOOK_URL` through (empty = disabled).

### 10.3 Hardening (found in the re-analysis)
- Deploy workflow: removed `podman image prune -f` (host-wide image deletion on shared hosts); `PROD_API_KEY` missing now prints a warning instead of silently deploying unauthenticated.
- `pytest.ini`: `asyncio_default_fixture_loop_scope = function` (warning gone).
- `docker-compose.yml` / `docker-compose.prod.yml`: `AUDIT_LOG_WEBHOOK_URL` passthrough.

### 10.4 Tests
- API (+10): reversal on/off, reversal creates owe transaction, sub-limit settle doesn't reverse, settings flags, audit disabled by default, audit fires for owe+settle+reverse, audit failure resilience, mention-neutralising payload.
- Bot (+3): reversal line shown on settle, on cashout, and omitted when absent.

**Result: 137 tests pass.**
