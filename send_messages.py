import discord
async def send_error_message(interaction, title, description):
    embed = discord.Embed(title=title, description=description, color=discord.Color.red())
    await interaction.followup.send(embed=embed)

async def send_success_message(interaction, title, description):
    embed = discord.Embed(title=title, description=description, color=discord.Color.green())
    await interaction.followup.send(embed=embed)

async def send_info_message(interaction, title, description):
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
    await interaction.followup.send(embed=embed)

async def send_two_column_table_message(interaction, title, description, data):
    # Split data into chunks of 25 rows (Discord's limit for embed fields)
    chunk_size = 25
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

    for i, chunk in enumerate(chunks):
        embed = discord.Embed(
            title=f"{title} (Page {i + 1}/{len(chunks)})",
            description=description if i == 0 else None,  # Only include description in the first embed
            color=discord.Color.yellow()
        )

        # Prepare the columns for the table
        names = "\n".join([row["name"] for row in chunk])
        owes = "\n".join([str(row["Owes"]) for row in chunk])
        is_owed = "\n".join([str(row["Is Owed"]) for row in chunk])

        # Add the columns as fields
        embed.add_field(name="Name", value=names, inline=True)
        embed.add_field(name="Owes", value=owes, inline=True)
        embed.add_field(name="Is Owed", value=is_owed, inline=True)

        # Send the embed
        if i == 0:
            # For the first embed, use followup.send
            await interaction.followup.send(embed=embed)
        else:
            # For subsequent embeds, send them as additional messages
            await interaction.channel.send(embed=embed)
        
async def send_one_column_table_message(interaction, title, description, data):
    # Split data into chunks of 25 rows (Discord's limit for embed fields)
    chunk_size = 25
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

    for i, chunk in enumerate(chunks):
        embed = discord.Embed(
            title=f"{title} (Page {i + 1}/{len(chunks)})",
            description=description if i == 0 else None,  # Only include description in the first embed
            color=discord.Color.yellow()
        )

        # Prepare the columns for the table
        settings = "\n".join([row["Setting"] for row in chunk])
        values = "\n".join([str(row["Value"]) for row in chunk])

        # Add the columns as fields
        embed.add_field(name="Setting", value=settings, inline=True)
        embed.add_field(name="Value", value=values, inline=True)

        # Send the embed
        if i == 0:
            # For the first embed, use followup.send
            await interaction.followup.send(embed=embed)
        else:
            # For subsequent embeds, send them as additional messages
            await interaction.channel.send(embed=embed)