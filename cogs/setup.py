import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.app_commands import Choice
from discord.ui import View, Button, Select

from utils.config import Config
from utils.embed import create_embed

config = Config()

class Setup(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(name="server_setup", description="Setup the server's embed messages.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(option=[
        Choice(name="Rules", value=1),
        Choice(name="Ticket", value=2),
        Choice(name="Roles", value=3)
    ])
    async def server_setup(self, interaction: Interaction, option: Choice[int]) -> None:
        if option.value == 1:
            await self._send_rules_embed(interaction)
        elif option.value == 2:
            await self._send_ticket_embed(interaction)
        elif option.value == 3:
            await self._send_roles_embed(interaction)
        await interaction.response.send_message("Message got sent", ephemeral=True)

    async def _send_rules_embed(self, interaction: Interaction) -> None:
        rules_description = (
            "Please **read** the **rules**; ignorance will **not** protect you from **punishment**.\n"
            "The team reserves the right to edit the rules at any time without warning.\n\n"
            "__**Discord Terms of Service and Guidelines**__\n"
            "• [Terms of Service](https://discord.com/terms)\n"
            "• [Guidelines](https://discord.com/guidelines)"
        )
        embed = create_embed(title="Rules", description=rules_description)
        embed.add_field(
            name="__General rules__",
            value=(
                ">>> **§1 →** Follow instructions from moderators and admins to avoid a kick or ban.\n"
                "**§2 →** Ban evasion with an alternative account will be reported.\n"
                "**§3 →** Avoid excessive special characters or inappropriate content in usernames.\n"
                "**§4 →** Unauthorized advertising is forbidden.\n"
                "**§5 →** Homophobic statements or profile pictures are not allowed.\n"
                "**§6 →** Senseless ticket creation may result in a warning."
            )
        )
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/696493395690127463/812912475954741248/unknown.png?width=1342&height=755")
        embed.set_image(url="https://cdn.discordapp.com/attachments/847594343450935356/1121540957154836614/twitter_header_photo_2.png")
        view = View(timeout=None)
        view.add_item(Button(style=discord.ButtonStyle.url, url="https://discord.com/terms", label="Terms of Service"))
        view.add_item(Button(style=discord.ButtonStyle.url, url="https://discord.com/guidelines", label="Guidelines"))
        await interaction.channel.send(embed=embed, view=view)

    async def _send_ticket_embed(self, interaction: Interaction) -> None:
        embed = create_embed(
            title="Create a Ticket",
            description="If you want to create a ticket, choose the service you need",
            timestamp=False
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/847594343450935356/1121540957154836614/twitter_header_photo_2.png")
        options = [
            discord.SelectOption(label="Discord Bots", value="discord"),
            discord.SelectOption(label="Endpoints", value="endpoints"),
            discord.SelectOption(label="Redirect to SNKRS App", value="redirect"),
            discord.SelectOption(label="Toolbox", value="toolbox"),
            discord.SelectOption(label="Custom Monitors", value="monitor"),
            discord.SelectOption(label="Other", value="other")
        ]
        select = Select(custom_id="ticket", placeholder="What Service do you need?", options=options)
        view = View(timeout=None)
        view.add_item(select)
        await interaction.channel.send(embed=embed, view=view)

    async def _send_roles_embed(self, interaction: Interaction) -> None:
        embed = create_embed(
            title="Roles",
            description="Choose your **roles** to get notified on announcements or polls.",
            timestamp=False
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/847594343450935356/1121540957154836614/twitter_header_photo_2.png")
        options = [
            discord.SelectOption(label="Announcements", value="announcements"),
            discord.SelectOption(label="Polls", value="polls")
        ]
        select = Select(custom_id="roles", placeholder="Select your role", options=options)
        view = View(timeout=None)
        view.add_item(select)
        await interaction.channel.send(embed=embed, view=view)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Setup(client))
