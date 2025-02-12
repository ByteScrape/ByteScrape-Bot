import os

import discord
from discord.ext import commands
from discord import app_commands

from cogs.github import local_repo_autocomplete
from utils.config import Config
from utils.logger import logger

config = Config()


class SellSystem(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(
        name="sell",
        description="Select a locally downloaded repository to send it in the channel."
    )
    @app_commands.autocomplete(repo=local_repo_autocomplete)
    @app_commands.checks.has_permissions(administrator=True)
    async def sell(self, interaction: discord.Interaction, repo: str):
        projects_dir = "./repositories"
        file_path = os.path.join(projects_dir, f"{repo}.zip")
        if not os.path.exists(file_path):
            await interaction.response.send_message(f"Local repository `{repo}` not found.", ephemeral=True)
            return
        try:
            file = discord.File(file_path, filename=f"{repo}.zip")
            await interaction.response.send_message(content=f"Here's the Product **{repo}**:", file=file)
        except Exception as e:
            logger.error(f"Error sending repository {repo}: {e}")
            await interaction.response.send_message("Error sending the repository file.", ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(SellSystem(client))
