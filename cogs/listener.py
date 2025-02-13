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
        if interaction.type == InteractionType.application_command:
            return  # Ignore application commands

        custom_id = interaction.data.get("custom_id")
        if not custom_id:
            return  # Ignore interactions without custom IDs

        if custom_id in ["ticket", "yes", "no", "close"]:
            handler = TicketHandler(interaction=interaction, client=self.client)
            await handler.manage()

        elif custom_id == "roles":
            added_roles = []
            for role_id in interaction.data["values"]:
                try:
                    role = discord.utils.get(interaction.guild.roles,
                                             id=int(config.config["bot"]["ids"]["roles"][str(role_id)]))
                    if role:  # Check if the role was found
                        await interaction.user.add_roles(role)
                        added_roles.append(role.name)
                    else:
                        logger.warning(f"Role with ID {role_id} not found in config.")
                        await interaction.response.send_message(f"One or more roles could not be added (invalid config).", ephemeral=True)
                        return

                except Exception as e:
                    logger.error(f"Error adding role: {e}")
                    await interaction.response.send_message("Failed to add one or more roles.", ephemeral=True)
                    return

            if added_roles: # Only send a message if roles were actually added
                await interaction.response.send_message(f"Added roles: {', '.join(added_roles)}.", ephemeral=True)

        elif custom_id == "paid":
            subscription_channel = self.client.get_channel(int(config.subscriptions_id))
            if not subscription_channel:
                await interaction.response.send_message("Subscription channel not found.", ephemeral=True)
                return

            user_id = interaction.user.id
            embed = create_embed(
                title="Payment Confirmation Request",
                description=f"User <@{user_id}> has submitted a payment confirmation. Please verify.",
                color=discord.Color.orange().value
            )
            confirm_button = Button(label="Confirm Payment", style=ButtonStyle.green, custom_id=f"confirm,{user_id}")
            view = View(timeout=None)
            view.add_item(confirm_button)
            await subscription_channel.send(embed=embed, view=view)
            await interaction.response.send_message("Your payment confirmation request has been submitted.", ephemeral=True)

        elif custom_id == "cancel":
            subscription_channel = self.client.get_channel(int(config.subscriptions_id))  # Consistent variable name
            if not subscription_channel:
                await interaction.response.send_message("Subscription channel not found.", ephemeral=True)
                return

            user_id = interaction.user.id
            embed = create_embed(
                title="Subscription Cancellation Request",
                description=f"User <@{user_id}> has requested a subscription cancellation. Please verify.",
                color=discord.Color.red().value
            )
            confirm_cancel_button = Button(label="Confirm Cancellation", style=ButtonStyle.red,
                                           custom_id=f"confirm_cancel,{user_id}")
            view = View(timeout=None)
            view.add_item(confirm_cancel_button)
            await subscription_channel.send(embed=embed, view=view)
            await interaction.response.send_message("Your cancellation request has been submitted.", ephemeral=True)

        elif custom_id.startswith("confirm_cancel,"):
            try:
                confirm_user_id = int(custom_id.split(",")[1])
            except (ValueError, IndexError):
                await interaction.response.send_message("Invalid cancellation request data.", ephemeral=True)
                return

            db = mongodb.get_database("ByteScrape")
            subs = db["subscriptions"]
            result = await subs.delete_one({"_id": confirm_user_id})
            now = datetime.datetime.now()

            if result.deleted_count == 1:
                embed = create_embed(color=discord.Color.dark_red().value, title="Subscription Cancelled",
                                     description=f"Subscription for <@{confirm_user_id}> has been cancelled on {now.strftime('%Y-%m-%d')}.")
                await interaction.response.edit_message(embed=embed, view=None)
            else:
                await interaction.response.send_message("Subscription not found.", ephemeral=True) # More accurate message
            return

        elif custom_id.startswith("confirm,"):
            subscription_channel = self.client.get_channel(int(config.subscriptions_id))
            if not subscription_channel:
                await interaction.response.send_message("Subscription channel not found.", ephemeral=True)
                return

            try:
                confirm_user_id = int(custom_id.split(",")[1])
            except (ValueError, IndexError):
                await interaction.response.send_message("Invalid payment confirmation data.", ephemeral=True)
                return

            now = datetime.datetime.now()
            db = mongodb.get_database("ByteScrape")
            subs = db["subscriptions"]

            doc = await subs.find_one({"_id": confirm_user_id})
            if not doc:
                await interaction.response.send_message("Subscription not found for this user.", ephemeral=True)
                return

            interval = doc.get("interval", 1)
            email = doc.get("email")
            user = self.client.get_user(confirm_user_id)
            next_payment = now + relativedelta(months=interval)

            result = await subs.update_one(
                {"_id": confirm_user_id},
                {"$set": {"last_paid": now, "next_payment": next_payment}}
            )

            if result.modified_count == 1:
                embed = create_embed(title="Payment Confirmed", color=discord.Color.green().value,
                                     description=f"Payment confirmed for <@{confirm_user_id}>.\n"
                                                 f"Last paid: {now.strftime('%Y-%m-%d')}\n"
                                                 f"Next payment: {next_payment.strftime('%Y-%m-%d')}")

                await subscription_channel.send(embed=embed)
                await interaction.response.send_message("Payment confirmed.", ephemeral=True)

                if user:  # Check if the user is available
                    try:
                        await user.send(embed=embed)
                    except Exception as e:
                        logger.error(f"Failed to send payment confirmation message to {user.id} | {user.name}: {e}")
                else:
                    logger.warning(f"User {confirm_user_id} not found.")

                if email: # Check if the email exists
                    async with PterodactylAPI() as api:
                        try:
                            await api.unsuspend_servers_by_email(email)
                        except Exception as e:
                            logger.error(f"Error suspending servers for {email}: {e}")
                            await asyncio.sleep(15) # Retry after a delay
                            try:
                                await api.unsuspend_servers_by_email(email)
                            except Exception as e:
                                logger.error(f"Failed to suspend servers for {email} after retry: {e}")
                else:
                    logger.warning(f"No email found for user {confirm_user_id}.")
            else:
                await interaction.response.send_message("Failed to update payment information.", ephemeral=True)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Listener(client))