import asyncio
import os

import aiofiles
import aiohttp
import discord
from discord.ext import commands
from discord import ButtonStyle, app_commands
from discord.ui import Button, View
from utils.config import Config
from utils.database import mongodb
from utils.embed import create_embed
from utils.logger import logger

config = Config()


async def get_repos() -> list:
    api_url = f"https://api.github.com/orgs/{config.github_organisation}/repos"
    headers = {"Authorization": f"token {config.github_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            if response.status == 200:
                repos_data = await response.json()
                return repos_data
            else:
                logger.error(f"Failed to get repos. Status: {response.status}")
                return []


async def download_repo(repo_name: str) -> (bool, str):
    download_url = f"https://api.github.com/repos/{config.github_organisation}/{repo_name}/zipball"
    headers = {"Authorization": f"token {config.github_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(download_url, headers=headers) as response:
            if response.status == 200:
                projects_dir = "./repositories"
                if not os.path.exists(projects_dir):
                    os.makedirs(projects_dir)
                zip_filename = os.path.join(projects_dir, f"{repo_name}.zip")
                async with aiofiles.open(zip_filename, "wb") as out_file:
                    content = await response.read()
                    await out_file.write(content)
                logger.info(f"Pulled {repo_name}")
                return True, f"Repository `{repo_name}` pulled successfully."
            else:
                logger.error(f"Error while trying to pull {repo_name} (status {response.status})")
                return False, f"Error: {response.status} while pulling `{repo_name}`."


async def repo_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    repos_data = await get_repos()
    choices = []
    for repo in repos_data:
        repo_name = repo.get("name")
        if current.lower() in repo_name.lower():
            choices.append(app_commands.Choice(name=repo_name, value=repo_name))
        if len(choices) >= 25:
            break
    return choices


async def local_repo_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    projects_dir = "./repositories"
    choices = []
    if os.path.exists(projects_dir):
        for filename in os.listdir(projects_dir):
            if filename.endswith(".zip"):
                local_repo_name = filename[:-4]  # Remove the .zip extension
                if current.lower() in local_repo_name.lower():
                    choices.append(app_commands.Choice(name=local_repo_name, value=local_repo_name))
                if len(choices) >= 25:
                    break
    return choices

class Github(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(
        name="pull-repo",
        description="Pull a GitHub repository by choosing from a list of available repos."
    )
    @app_commands.autocomplete(repo=repo_autocomplete)
    @app_commands.checks.has_permissions(administrator=True)
    async def pull_repo(self, interaction: discord.Interaction, repo: str):
        success, message = await download_repo(repo)
        await interaction.response.send_message(message, ephemeral=True)

    @app_commands.command(
        name="pull-all-repos",
        description="Pull all available GitHub repositories."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def pull_all_repos(self, interaction: discord.Interaction):
        try:
            repos_data = await get_repos()
            if not repos_data:
                return await interaction.response.send_message("No repositories found to pull.", ephemeral=True)

            # Launch downloads concurrently for all repositories
            tasks = [download_repo(repo.get("name")) for repo in repos_data]
            results = await asyncio.gather(*tasks)
            success_count = sum(1 for success, _ in results if success)
            fail_count = len(results) - success_count
            summary = f"Pulled {success_count} repositories successfully. Failed: {fail_count}"
            await interaction.response.send_message(summary, ephemeral=True)

        except Exception as e:
            logger.error(f"Something went wrong: {e}")

    @app_commands.command(
        name="list-repos",
        description="List all repositories from the GitHub organization in a numbered list."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def list_repos(self, interaction: discord.Interaction):
        repos_data = await get_repos()
        if not repos_data:
            await interaction.response.send_message("No repositories found.", ephemeral=True)
            return
        repo_names = [repo.get("name") for repo in repos_data]
        numbered_list = "\n".join(f"**{i})** {name}" for i, name in enumerate(repo_names, start=1))
        embed = create_embed(title="Repositories", description=numbered_list)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="list-local-repos",
        description="List all locally downloaded repositories in a numbered list."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def list_local_repos(self, interaction: discord.Interaction):
        projects_dir = "./repositories"
        if not os.path.exists(projects_dir):
            await interaction.response.send_message("Repositories folder does not exist.", ephemeral=True)
            return
        repo_files = [filename for filename in os.listdir(projects_dir) if filename.endswith(".zip")]
        if not repo_files:
            await interaction.response.send_message("No local repositories found.", ephemeral=True)
            return
        # Remove the .zip extension and enumerate the list
        repo_names = [filename[:-4] for filename in repo_files]
        numbered_list = "\n".join(f"**{i})** {name}" for i, name in enumerate(repo_names, start=1))
        embed = create_embed(title="Local Repositories", description=numbered_list)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="remove-repo",
        description="Remove a locally stored repository from the repositories folder."
    )
    @app_commands.autocomplete(repo=local_repo_autocomplete)
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_repo_local(self, interaction: discord.Interaction, repo: str):
        projects_dir = "./repositories"
        target_file = os.path.join(projects_dir, f"{repo}.zip")
        if os.path.exists(target_file):
            try:
                os.remove(target_file)
                logger.info(f"Removed local repository file: {repo}.zip")
                await interaction.response.send_message(f"Local repository `{repo}` removed successfully.",
                                                        ephemeral=True)
            except Exception as e:
                logger.error(f"Failed to remove {repo}.zip: {e}")
                await interaction.response.send_message(f"Error removing local repository `{repo}`.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Local repository `{repo}` not found.", ephemeral=True)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Github(client))
