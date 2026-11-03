"""Architecture guard tests.

These tests protect the layering that makes the bot multi-platform:

- ``bot.platform`` (protocols), ``bot.commands`` (handlers),
  ``bot.utilities`` (pure helpers) and ``bot.setup`` (registry) must not
  import any chat-platform SDK.
- Adapters in ``bot/platforms/<platform>/`` implement the protocols.
- ``bot.pint_bot`` dispatches on the PLATFORM env var.
"""
import inspect
from pathlib import Path

import pytest

import bot.pint_bot as dispatcher
from bot.platform.context import CommandContext, PlatformUser
from bot.platform.messenger import Messenger

REPO_ROOT = Path(__file__).resolve().parent.parent

SHARED_LAYERS = ["bot/commands", "bot/platform", "bot/utilities", "bot/setup", "bot/pint_bot.py"]

PLATFORM_SDK_IMPORTS = ("discord", "telegram", "aiogram", "slack_sdk", "slack_bolt")


def _python_files(layer: str):
    if layer.endswith(".py"):
        yield Path(layer)
        return
    yield from (REPO_ROOT / layer).rglob("*.py")


def test_shared_layers_do_not_import_platform_sdks():
    violations = []
    for layer in SHARED_LAYERS:
        for py_file in _python_files(layer):
            source = py_file.read_text()
            for sdk in PLATFORM_SDK_IMPORTS:
                for line in source.splitlines():
                    stripped = line.strip()
                    if stripped.startswith(f"import {sdk}") or stripped.startswith(f"from {sdk}"):
                        violations.append(f"{py_file}: {line.strip()}")
    assert not violations, "Platform SDK import(s) found in shared layers:\n" + "\n".join(violations)


def test_discord_adapter_satisfies_protocols():
    discord = pytest.importorskip("discord")
    from unittest.mock import MagicMock
    from bot.platforms.discord.context import DiscordCommandContext, platform_user_from_discord

    interaction = MagicMock()
    interaction.user.id = 123
    interaction.user.display_name = "TestUser"
    interaction.user.mention = "<@123>"
    interaction.client.user.id = 0

    ctx = DiscordCommandContext(interaction)
    assert isinstance(ctx, CommandContext)
    assert isinstance(ctx.messenger, Messenger)
    assert ctx.user_id == "123"
    assert ctx.user_display_name == "TestUser"

    user = platform_user_from_discord(interaction.user)
    assert user == PlatformUser(id="123", display_name="TestUser", mention="<@123>")


def test_null_platform_user():
    user = PlatformUser(id="1", display_name="n", mention="m")
    assert user.id == "1"


def test_dispatcher_rejects_unknown_platform(monkeypatch):
    monkeypatch.setenv("PLATFORM", "telegram")
    with pytest.raises(SystemExit):
        dispatcher.main()


def test_dispatcher_defaults_to_discord(monkeypatch):
    monkeypatch.delenv("PLATFORM", raising=False)
    calls = []

    import bot.platforms.discord.bot as discord_bot
    monkeypatch.setattr(discord_bot, "main", lambda: calls.append("discord"))
    dispatcher.main()
    assert calls == ["discord"]
