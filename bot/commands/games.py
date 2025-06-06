import discord
from bot import config
import bot.utilities.send_messages as send_messages

async def handle_roll(interaction: discord.Interaction):
    await interaction.response.defer()
    user = interaction.user

    volcano_number = config.RANDOM_NUMBER_GENERATOR.randint(1, config.ROLL_WINNING_NUMBER)
    if volcano_number == config.ROLL_WINNING_NUMBER:
        await send_messages.send_success_message(
            interaction,
            title=f"WINNER! You rolled {volcano_number}!",
            description=f"Congratulations {user.mention}!\nYou won the {config.ROLL_COMMAND} game!\n"
        )
    else:
        await send_messages.send_info_message(
            interaction,
            title=f"You rolled {volcano_number}.",
            description=f"Sorry {user.mention}, that's not a winning number.\nBetter luck next time!"
        )
