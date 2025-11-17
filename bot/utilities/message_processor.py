"""Discord bot message processor that processes and actually sends messages."""
import discord
import bot.config as config

async def send_message(
    interaction: discord.Interaction,
    title: str,
    description: str,
    color: discord.Color,
    ephermal: bool = False
):
    """Sends an embed message, splitting into multiple messages if the description is too long.
    Splits at newlines only if needed."""
    await check_title_length(interaction, title, ephermal)

    # If description fits, send directly without splitting
    if len(description) <= config.DISCORD_EMBED_DESCRIPTION_LIMIT:
        embed = discord.Embed(title=title, description=description, color=color)

        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=ephermal)
        else:
            await interaction.followup.send(embed=embed, ephemeral=ephermal)
    else:
        await split_message_and_send(interaction,title,description,color,ephermal)

async def check_title_length(interaction: discord.Interaction, title: str, ephermal:bool):
    """Checks the title matches discord character limits"""
    if len(title) > config.DISCORD_EMBED_TITLE_LIMIT:
        await send_message(
            interaction,
            "", #this is blank to prevent infinite loop if DISCORD_EMBED_TITLE_LIMIT is set to a low number
            f"Title exceeds Discord's {config.DISCORD_EMBED_TITLE_LIMIT} character limit. Sorry about that",
            discord.Color.red(),
            ephermal
        )


async def split_message_and_send(
    interaction: discord.Interaction,
    title: str,
    description: str,
    color: discord.Color,
    ephermal: bool
):
    """Sends a split message across multiple embeds"""
    chunks = split_text_into_chunks(description, config.DISCORD_EMBED_DESCRIPTION_LIMIT)

    await send_embed_chunks(interaction, title, chunks, color, ephermal)


def split_text_into_chunks(text: str, limit: int) -> list[str]:
    """Splits a long text into chunks that fit within Discord embed limits."""
    chunks = []
    current_chunk = ""

    for paragraph in text.split('\n'):
        current_chunk, new_chunks = process_paragraph(paragraph, current_chunk, limit)
        chunks.extend(new_chunks)

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def process_paragraph(paragraph: str, current_chunk: str, limit: int) -> tuple[str, list[str]]:
    """Processes a paragraph and decides whether to start a new chunk or continue the current one."""
    chunks = []
    to_add = ("\n" if current_chunk else "") + paragraph

    if len(current_chunk) + len(to_add) > limit:
        if current_chunk:
            chunks.append(current_chunk)

        if len(paragraph) > limit:
            chunks.extend(chunk_paragraph(paragraph, limit))
            return "", chunks

        return paragraph, chunks

    return current_chunk + to_add, chunks


def chunk_paragraph(paragraph: str, limit: int) -> list[str]:
    """Splits a single long paragraph into smaller parts."""
    return [paragraph[i:i + limit] for i in range(0, len(paragraph), limit)]


async def send_embed_chunks(
    interaction: discord.Interaction,
    title: str,
    chunks: list[str],
    color: discord.Color,
    ephermal: bool = False
    ):
    """Sends the embed messages one by one, including the title only in the first."""
    for i, chunk in enumerate(chunks):
        embed = discord.Embed(
            title=title if i == 0 else None,
            description=chunk,
            color=color
        )
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=ephermal)
        else:
            await interaction.followup.send(embed=embed, ephemeral=ephermal)
