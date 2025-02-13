import asyncio
import datetime

import discord
from dateutil.relativedelta import relativedelta
from discord import InteractionType, Interaction, ButtonStyle
from discord.ext import commands
from discord.ui import Button, View

from utils.config import Config
from utils.database import mongodb
from utils.embed import create_embed
from utils.logger import logger
from utils.pterodactyl import PterodactylAPI
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

        custom_id = interaction.data.get("custom_id")
        if not custom_id:
            return

        if interaction.data in ["ticket", "yes", "no", "close", "roles"]:
            handler = TicketHandler(interaction=interaction, client=self.client)
            await handler.manage()
        if custom_id == "paid":
            subscription_channel = self.client.get_channel(int(config.subscriptions_id))
            if subscription_channel is None:
                await interaction.response.send_message("Subscription channel not found.", ephemeral=True)
                return

            user_id = interaction.user.id
            embed = create_embed(
                title="Payment Confirmation",
                description=f"User <@{user_id}> claims to have paid. Please confirm.",
                color=discord.Color.orange().value
            )
            # Create a confirm button with custom ID "confirm,{user_id}"
            confirm_button = Button(label="Confirm", style=ButtonStyle.green, custom_id=f"confirm,{user_id}")
            view = View(timeout=None)
            view.add_item(confirm_button)
            await subscription_channel.send(embed=embed, view=view)
            await interaction.response.send_message("Your payment claim has been submitted.", ephemeral=True)

            # Handle the "cancel" button
        elif custom_id == "cancel":
            channel = self.client.get_channel(int(config.subscriptions_id))
            if channel:
                user_id = interaction.user.id
                embed = create_embed(
                    title="Cancellation Request",
                    description=f"User <@{user_id}> wants to cancel their product. Please confirm cancellation.",
                    color=discord.Color.red().value
                )
                # Create a confirm button for cancellation with custom_id "confirm_cancel,{user_id}"
                confirm_cancel_button = Button(label="Confirm Cancellation", style=ButtonStyle.red,
                                               custom_id=f"confirm_cancel,{user_id}")
                view = View(timeout=None)
                view.add_item(confirm_cancel_button)
                await channel.send(embed=embed, view=view)
                await interaction.response.send_message("Your cancellation request has been submitted.", ephemeral=True)
            return

            # Handle confirm cancellation
        elif custom_id.startswith("confirm_cancel,"):
            parts = custom_id.split(",")
            if len(parts) != 2:
                await interaction.response.send_message("Invalid confirmation data.", ephemeral=True)
                return
            try:
                confirm_user_id = int(parts[1])
            except ValueError:
                await interaction.response.send_message("Invalid user ID in confirmation.", ephemeral=True)
                return

            # Delete the user's subscription from the database
            db = mongodb.get_database("ByteScrape")
            subs = db["subscriptions"]
            result = await subs.delete_one({"_id": confirm_user_id})
            now = datetime.datetime.now()

            if result.deleted_count == 1:
                embed = create_embed(color=discord.Color.dark_red().value, title="Subscription Cancellation",
                                     description=f"Subscription for <@{confirm_user_id}> has been cancelled on {now.strftime('%Y-%m-%d')}.")
                await interaction.response.edit_message(embed=embed, view=None)
            else:
                await interaction.response.send_message("Failed to delete the subscription.", ephemeral=True)
            return

            # Handle the confirm button (custom ID starts with "confirm,")
        elif custom_id.startswith("confirm,"):
            subscription_channel = self.client.get_channel(int(config.subscriptions_id))
            if subscription_channel is None:
                await interaction.response.send_message("Subscription channel not found.", ephemeral=True)
                return
            parts = custom_id.split(",")
            if len(parts) != 2:
                await interaction.response.send_message("Invalid confirmation data.", ephemeral=True)
                return

            try:
                confirm_user_id = int(parts[1])
            except ValueError:
                await interaction.response.send_message("Invalid user ID.", ephemeral=True)
                return

            now = datetime.datetime.now()
            db = mongodb.get_database("ByteScrape")
            subs = db["subscriptions"]

            # Retrieve the user's subscription document
            doc = await subs.find_one({"_id": confirm_user_id})
            if doc is None:
                await interaction.response.send_message("Subscription not found for the user.", ephemeral=True)
                return

            # Use the saved interval in months to calculate the next payment date
            interval = doc.get("interval", 1)  # Default to 1 month if missing
            email = doc.get("email")
            user = self.client.get_user(confirm_user_id)
            next_payment = now + relativedelta(months=interval)

            result = await subs.update_one(
                {"_id": confirm_user_id},
                {"$set": {"last_paid": now, "next_payment": next_payment}}
            )
            if result.modified_count == 1:
                embed = create_embed(title="Payment Confirmation", color=discord.Color.green().value,
                                     description=f"Payment confirmed for <@{confirm_user_id}>.\n"
                                                 f"Last paid: {now.strftime('%Y-%m-%d')}\n"
                                                 f"Next payment: {next_payment.strftime('%Y-%m-%d')}")

                await subscription_channel.send(embed=embed)

                await interaction.response.send_message("The payment has been confirmed.", ephemeral=True)

                try:
                    await user.send(embed=embed)
                except Exception:
                    logger.error(f"Failed to send subscription confirmation message to {user.id} | {user.name}")

                if email is None:
                    logger.error(f"No email found for suspended subscription for {user.id} | {user.name}")
                else:
                    async with PterodactylAPI() as api:
                        try:
                            await api.unsuspend_servers_by_email(email)
                        except Exception as e:
                            logger.error("Error:", e)
                            await asyncio.sleep(15)
                            await api.unsuspend_servers_by_email(email)

            else:
                await interaction.response.send_message("Failed to update the subscription.", ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Listener(client))
