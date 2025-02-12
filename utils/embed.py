from datetime import datetime

import discord

from utils.config import Config

config = Config()


def create_embed(color=config.color, timestamp:bool=config.timestamp, **kwargs):
    embed = discord.Embed(color=int(color, 16), **kwargs)
    if timestamp:
        embed.timestamp = datetime.now()
    embed.set_footer(text=config.footer_text, icon_url=config.footer_icon)
    return embed
