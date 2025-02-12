from datetime import datetime

import discord

from utils.config import Config

config = Config()


def create_embed(color=config.color, timestamp:bool=config.timestamp, **kwargs):
    cl = None
    if color == config.color:
        cl = int(config.color, 16)
    else:
        cl = color
    embed = discord.Embed(color=cl, **kwargs)
    if timestamp:
        embed.timestamp = datetime.now()
    embed.set_footer(text=config.footer_text, icon_url=config.footer_icon)
    return embed
