"""Entry point for the bot.

Selects the chat platform via the ``PLATFORM`` environment variable
(default: ``discord``). To add another platform (e.g. Telegram), see
``docs/ADDING_A_PLATFORM.md`` — implement the adapter under
``bot/platforms/<name>/`` and register it here.
"""
import os
import sys

SUPPORTED_PLATFORMS = ("discord",)

def main():
    """Dispatch to the configured platform adapter."""
    platform = os.getenv("PLATFORM", "discord").strip().lower()

    if platform == "discord":
        from bot.platforms.discord.bot import main as run_discord
        run_discord()
        return

    sys.exit(
        f"Unsupported PLATFORM={platform!r}. Supported platforms: {', '.join(SUPPORTED_PLATFORMS)}.\n"
        "To add a new platform, see docs/ADDING_A_PLATFORM.md."
    )

if __name__ == "__main__":
    main()
