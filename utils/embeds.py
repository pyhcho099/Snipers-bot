import discord
from typing import Optional

def create_success_embed(title: str, description: str, **kwargs) -> discord.Embed:
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=0x57f287
    )
    for key, value in kwargs.items():
        embed.add_field(name=key, value=value, inline=False)
    return embed

def create_error_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=0xed4245
    )

def create_info_embed(title: str, description: str, **kwargs) -> discord.Embed:
    embed = discord.Embed(
        title=f"ℹ️ {title}",
        description=description,
        color=0x5865f2
    )
    for key, value in kwargs.items():
        embed.add_field(name=key, value=value, inline=False)
    return embed
