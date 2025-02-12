import discord
from discord import app_commands
from discord.ext import commands


class TestCog(commands.Cog):
    def __init__(self, client) -> None:
        self.client = client

    @app_commands.command(name="test")
    async def test_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("Test command",
                                                ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TestCog(bot))
