"""Abstract platform types for the bot.

The command handlers in ``bot.commands`` and the helpers in
``bot.utilities`` are written against the protocols defined here.
Each chat platform (Discord, and future Telegram, ...) provides a
concrete adapter in ``bot/platforms/<platform>/``.
"""
from bot.platform.context import CommandContext, PlatformUser
from bot.platform.messenger import Messenger

__all__ = ["CommandContext", "PlatformUser", "Messenger"]
