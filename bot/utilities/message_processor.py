"""Discord bot message processor that processes and actually sends messages."""
import discord
import bot.config as config

async def send_message(
    interaction: discord.Interaction,
    title: str,
    description: str,
    color: discord.Color
):
    """Sends an embed message, splitting into multiple messages if the description is too long.
    Splits at newlines only if needed."""
    await check_title_length(interaction, title)

    # If description fits, send directly without splitting
    if len(description) <= config.DISCORD_EMBED_DESCRIPTION_LIMIT:
        embed = discord.Embed(title=title, description=description, color=color)
        await interaction.followup.send(embed=embed)
        return
    else:
        await split_message_and_send(interaction,title,description,color)

async def check_title_length(interaction: discord.Interaction, title: str):
    if len(title) > config.DISCORD_EMBED_TITLE_LIMIT:
            await send_message(
                interaction,
                "Formatting Error",
                f"Title exceeds Discord's {config.DISCORD_EMBED_TITLE_LIMIT} character limit. Sorry about that",
                discord.Color.red()
            )

async def split_message_and_send(
    interaction: discord.Interaction,
    title: str,
    description: str,
    color: discord.Color,
):
    def chunk_paragraph(paragraph: str, limit: int) -> list[str]:
        """Split a long paragraph into chunks that fit within the character limit."""
        return [paragraph[i:i + limit] for i in range(0, len(paragraph), limit)]

    def build_chunks(text: str, limit: int) -> list[str]:
        """Split full text into chunks that respect the embed description limit."""
        chunks = []
        current_chunk = ""
        for para in text.split('\n'):
            to_add = ("" if not current_chunk else "\n") + para
            if len(current_chunk) + len(to_add) > limit:
                if current_chunk:
                    chunks.append(current_chunk)
                if len(para) > limit:
                    chunks.extend(chunk_paragraph(para, limit))
                    current_chunk = ""
                else:
                    current_chunk = para
            else:
                current_chunk += to_add
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    chunks = build_chunks(description, config.DISCORD_EMBED_DESCRIPTION_LIMIT)

    # Send first embed with title
    await interaction.followup.send(embed=discord.Embed(title=title, description=chunks[0], color=color))

    # Send remaining embeds without title
    for chunk in chunks[1:]:
        await interaction.followup.send(embed=discord.Embed(description=chunk, color=color))