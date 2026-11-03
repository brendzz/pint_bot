"""Mini games. Platform-agnostic."""
from bot import config
from bot.platform.context import CommandContext

async def handle_roll(ctx: CommandContext):
    await ctx.defer()
    user_mention = ctx.user_mention

    volcano_number = config.RANDOM_NUMBER_GENERATOR.randint(1, config.ROLL_WINNING_NUMBER)
    if volcano_number == config.ROLL_WINNING_NUMBER:
        await ctx.messenger.success(
            ctx,
            title=f"WINNER! You rolled {volcano_number}!",
            description=f"Congratulations {user_mention}!\nYou won the {config.ROLL_COMMAND} game!\n"
        )
    else:
        await ctx.messenger.info(
            ctx,
            title=f"You rolled {volcano_number}.",
            description=f"Sorry {user_mention}, that's not a winning number.\nBetter luck next time!"
        )
