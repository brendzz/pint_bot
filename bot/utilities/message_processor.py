"""Discord bot message processor that processes and actually sends messages."""
import discord
import bot.config as config
from send_messages import send_error_message

async def send_message(
    interaction: discord.Interaction,
    title: str,
    description: str,
    color: discord.Color
):
    """Sends an embed message, splitting into multiple messages if the description is too long.
    Splits at newlines only if needed."""
    check_title_length(title)

    # If description fits, send directly without splitting
    if len(description) <= config.DISCORD_EMBED_DESCRIPTION_LIMIT:
        embed = discord.Embed(title=title, description=description, color=color)
        await interaction.followup.send(embed=embed)
        return
    else:
        split_message_and_send(interaction,title,description,color)

async def check_title_length(interaction: discord.Interaction, title: str):
    if len(title) > config.DISCORD_EMBED_TITLE_LIMIT:
            await send_error_message(
                interaction,
                "Formatting Error",
                f"Title exceeds Discord's {config.DISCORD_EMBED_TITLE_LIMIT} character limit. Sorry about that"
            )
            return

async def split_message_and_send(interaction: discord.Interaction,
    title: str,
    description: str,
    color: discord.Color):

      # Otherwise split by newlines and chunk
    paragraphs = description.split('\n')
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        to_add = ("" if current_chunk == "" else "\n") + para
        if len(current_chunk) + len(to_add) > config.DISCORD_EMBED_DESCRIPTION_LIMIT:
            if current_chunk:
                chunks.append(current_chunk)
            if len(para) > config.DISCORD_EMBED_DESCRIPTION_LIMIT:
                for i in range(0, len(para), config.DISCORD_EMBED_DESCRIPTION_LIMIT):
                    chunks.append(para[i:i + config.DISCORD_EMBED_DESCRIPTION_LIMIT])
                current_chunk = ""
            else:
                current_chunk = para
        else:
            current_chunk += to_add

    if current_chunk:
        chunks.append(current_chunk)

    # Send first embed with title
    first_embed = discord.Embed(title=title, description=chunks[0], color=color)
    await interaction.followup.send(embed=first_embed)

    # Send remaining embeds without title
    for chunk in chunks[1:]:
        embed = discord.Embed(description=chunk, color=color)
        await interaction.followup.send(embed=embed)
