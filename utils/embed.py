from datetime import datetime

import discord

from utils.config import Config

config = Config()


def create_embed(**kwargs):
    embed = discord.Embed(**kwargs)
    if config.timestamp:
        embed.timestamp = datetime.now()
    return embed