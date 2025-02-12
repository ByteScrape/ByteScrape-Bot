import discord
from discord import InteractionType, Interaction
from discord.ext import commands

from utils.config import Config
from utils.ticket_manager import TicketHandler

config = Config()

class Listener(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @commands.Cog.listener()
    async def on_interaction(self, interaction: Interaction) -> None:
        # Skip application commands
        if interaction.type == InteractionType.application_command:
            return
        handler = TicketHandler(interaction=interaction, client=self.client)
        await handler.manage()

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Listener(client))
