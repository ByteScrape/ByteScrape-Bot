import datetime

import discord
from discord.ext import commands

from utils.config import Config
from utils.embed import create_embed

config = Config()


class Welcome(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = discord.utils.get(member.guild.roles, id=int(config.member_id))

        await member.add_roles(role)

        channel = self.client.get_channel(config.welcome_id)

        embed = create_embed(
            title=f"Welcome {member.name}",
        )
        embed.set_thumbnail(url=member.avatar.url)
        return await channel.send(
            embed=embed
        )


async def setup(client):
    await client.add_cog(Welcome(client))
