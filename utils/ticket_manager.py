import asyncio
import datetime
import discord
from discord.ui import Button, View
from utils.config import Config
from utils.embed import create_embed  # Import your custom embed creator

class TicketHandler:
    def __init__(self, interaction: discord.Interaction, client: discord.Client) -> None:
        self.interaction = interaction
        self.client = client
        self.config = Config()

    async def ticket(self) -> None:
        # Determine the category via the selected service value
        service_value = self.interaction.data.get("values", [None])[0]
        category_id = int(self.config.config["bot"]["ids"]["categories"].get(service_value, 0))
        category = self.client.get_channel(category_id)
        channel = await self.interaction.guild.create_text_channel(
            name=f"{self.interaction.user.name}",
            category=category,
            topic=f"Ticket from {self.interaction.user.name}"
        )

        # Set permissions: disable for default role and enable for team and ticket creator
        await channel.set_permissions(
            self.interaction.guild.default_role,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_messages=False,
            external_emojis=True,
            read_message_history=True,
            external_stickers=True
        )
        team_role = self.interaction.guild.get_role(int(self.config.team_id))
        await channel.set_permissions(
            team_role,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_messages=True,
            external_emojis=True,
            read_message_history=True,
            external_stickers=True
        )
        await channel.set_permissions(
            self.interaction.user,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_messages=True,
            external_emojis=True,
            read_message_history=True,
            external_stickers=True
        )

        await self.interaction.response.send_message(f"Your Ticket got created {channel.mention}", ephemeral=True)

        # Create embed using the create_embed function
        embed = create_embed(
            title="Welcome to the Ticket area!",
            description="The Team will get back to you as soon as possible.",
        )

        close_button = Button(label="Close 🔒", custom_id="close")
        view = View(timeout=None)
        view.add_item(close_button)
        await channel.send(content=f"<@{self.interaction.user.id}>", embed=embed, view=view)

    async def yes(self) -> None:
        channel = self.client.get_channel(int(self.interaction.channel.id))
        await self.interaction.response.send_message("This channel gets deleted in 5 sec.", ephemeral=True)
        await asyncio.sleep(5)
        await channel.delete()

    async def no(self) -> None:
        await self.interaction.response.send_message("Canceled delete", ephemeral=True)

    async def close(self) -> None:
        yes_button = Button(label="Yes", style=discord.ButtonStyle.green, custom_id="yes")
        no_button = Button(label="No", style=discord.ButtonStyle.red, custom_id="no")
        view = View(timeout=120)
        view.add_item(yes_button)
        view.add_item(no_button)
        await self.interaction.response.send_message(
            "Are you sure you want to delete this ticket?",
            view=view,
            ephemeral=True
        )

    async def manage(self) -> None:
        actions = {
            "ticket": self.ticket,
            "yes": self.yes,
            "no": self.no,
            "close": self.close
        }
        custom_id = self.interaction.data.get("custom_id")
        action = actions.get(custom_id)
        if action:
            await action()
