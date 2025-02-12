import discord
from discord.ext import commands, tasks
from utils.config import Config
from utils.database import mongodb
from utils.logger import logger
from discord import ButtonStyle, app_commands
from discord.ui import Button, View
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

config = Config()


class Subscription(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.subscriptions = mongodb.get_database("ByteScrape")[
            "subscriptions"]  # Will assign this once the connection is ready
        self.check_subscriptions.start()

    def cog_unload(self):
        self.check_subscriptions.cancel()

    @tasks.loop(hours=int(config.subscription_delay))
    async def check_subscriptions(self):
        current_time = datetime.now()

        async for document in self.subscriptions.find({"next_payment": {"$lte": current_time}}):
            user_id = document.get("_id")
            due_date = document.get("next_payment")
            price = document.get("price")

            user = self.client.get_user(user_id)
            if user is not None:

                days_overdue = (current_time - due_date).days

                if days_overdue == 7:
                    embed = discord.Embed(title="Subscription Expired",
                                          description=f"Please renew your subscription to continue enjoying our services, your service will be **suspended tomorrow** if you do not pay.",
                                          color=int(config.color, 16))
                    embed.add_field(name="Expiry Date:", value=f"<t:{round(due_date.timestamp())}:D>",
                                    inline=True)
                    embed.add_field(name="Price:", value=f"{price}€", inline=True)
                    embed.add_field(name="Payment Method:", value="PayPal", inline=True)
                    embed.add_field(name="Service Suspended:", value="False", inline=True)
                    view = View()
                    button1 = Button(
                        label="Confirm Payment",
                        style=ButtonStyle.green,
                        custom_id=f"paid"
                    )
                    button2 = Button(
                        label="Cancel Payment",
                        style=ButtonStyle.red,
                        custom_id=f"cancel"
                    )
                    button3 = Button(
                        label="Paypal",
                        style=ButtonStyle.url,
                        url=config.paypal
                    )
                    view.add_item(button1)
                    view.add_item(button2)
                    view.add_item(button3)

                    try:
                        await user.send(embed=embed, view=view)
                    except Exception:
                        logger.error(f"Failed to send subscription expired message to {user.id} | {user.name}")
                    continue
                elif days_overdue > 7:
                    embed = discord.Embed(title="Subscription Expired",
                                          description=f"Please renew your subscription to continue enjoying our services, your service will **now** be **suspended**.",
                                          color=int(config.color, 16))
                    embed.add_field(name="Expiry Date:", value=f"<t:{round(due_date.timestamp())}:D>",
                                    inline=True)
                    embed.add_field(name="Price:", value=f"{price}€", inline=True)
                    embed.add_field(name="Payment Method:", value="PayPal", inline=True)
                    embed.add_field(name="Service Suspended:", value="True", inline=True)

                    view = View()
                    button1 = Button(
                        label="Confirm Payment",
                        style=ButtonStyle.green,
                        custom_id=f"paid"
                    )
                    button2 = Button(
                        label="Cancel Payment",
                        style=ButtonStyle.red,
                        custom_id=f"cancel"
                    )
                    button3 = Button(
                        label="Paypal",
                        style=ButtonStyle.url,
                        url=config.paypal
                    )
                    view.add_item(button1)
                    view.add_item(button2)
                    view.add_item(button3)
                    try:
                        await user.send(embed=embed, view=view)
                    except Exception:
                        logger.error(f"Failed to send subscription expired message to {user.id} | {user.name}")
                    continue
                elif 0 < days_overdue < 7:
                    embed = discord.Embed(title="Subscription Expired",
                                          description=f"Please renew your subscription to continue enjoying our services, your service will be **suspended** in **7 days**.",
                                          color=int(config.color, 16))
                    embed.add_field(name="Expiry Date:", value=f"<t:{round(due_date.timestamp())}:D>",
                                    inline=True)
                    embed.add_field(name="Price:", value=f"{price}€", inline=True)
                    embed.add_field(name="Payment Method:", value="PayPal", inline=True)
                    embed.add_field(name="Service Suspended:", value="False", inline=True)

                    view = View()
                    button1 = Button(
                        label="Confirm Payment",
                        style=ButtonStyle.green,
                        custom_id=f"paid"
                    )
                    button2 = Button(
                        label="Cancel Payment",
                        style=ButtonStyle.red,
                        custom_id=f"cancel"
                    )
                    button3 = Button(
                        label="Paypal",
                        style=ButtonStyle.url,
                        url=config.paypal
                    )
                    view.add_item(button1)
                    view.add_item(button2)
                    view.add_item(button3)

                    try:
                        await user.send(embed=embed, view=view)
                    except Exception:
                        logger.error(f"Failed to send subscription expired message to {user.id} | {user.name}")
                    continue

    @check_subscriptions.before_loop
    async def before_check(self):
        await self.client.wait_until_ready()
        logger.debug("Subscription check task starting...")

    @app_commands.command(
        name="add_subscription",
        description="Add a user subscription with a specified price and payment interval in months."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_subscription(self, interaction: discord.Interaction, user: discord.User, price: float, interval: int):
        now = datetime.utcnow()
        # Add the specified number of months to the current time.
        next_payment = now + relativedelta(months=interval)
        try:
            subscription_doc = {
                "_id": int(user.id),
                "price": price,
                "interval": interval,
                "last_paid": now,
                "next_payment": next_payment,
                "overdue_run": False
            }
            await self.subscriptions.insert_one(subscription_doc)
        except Exception as e:
            logger.error(f"Failed to add subscription for {user.id} | {user.name}: {e}")
            return await interaction.response.send_message("Failed to add subscription. Please try again later.",
                                                           ephemeral=True)

        return await interaction.response.send_message(
            f"Subscription added for {user.mention} with a price of {price:.2f}€ and a payment interval of {interval} months.",
            ephemeral=True
        )

    @app_commands.command(name="set_last_paid",
                          description="Set the last paid date for a user's subscription (DD-MM-YYYY).")
    @app_commands.describe(user="The user whose subscription last paid date should be updated.",
                           last_paid="The new last paid date (DD-MM-YYYY).")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_last_paid(self, interaction: discord.Interaction, user: discord.User, last_paid: str):
        try:
            last_paid_date = datetime.strptime(last_paid, "%d-%m-%Y")
        except ValueError:
            await interaction.response.send_message("Invalid date format. Use DD-MM-YYYY.", ephemeral=True)
            return

        # Retrieve the subscription document for the provided user.
        subscription_doc = await self.subscriptions.find_one({"_id": int(user.id)}
                                                             )
        if not subscription_doc:
            return await interaction.response.send_message(f"No subscription found for {user.mention}.", ephemeral=True)

        interval = subscription_doc.get("interval", 90)
        next_payment = last_paid_date + relativedelta(months=interval)
        try:
            await self.subscriptions.update_one(
                {"_id": int(user.id)},
                {"$set": {
                    "last_paid": last_paid_date,
                    "next_payment": next_payment,
                    "overdue_run": False
                }}
            )
        except Exception as e:
            logger.error(f"Failed to update subscription for {user.id} | {user.name}: {e}")
            return await interaction.response.send_message("Failed to update subscription. Please try again later.",
                                                           ephemeral=True)

        return await interaction.response.send_message(
            f"Last paid date for {user.mention} updated to {last_paid_date.strftime('%Y-%m-%d')}. "
            f"Next payment is due on {next_payment.strftime('%Y-%m-%d')}.",
            ephemeral=True
        )

    @app_commands.command(
        name="remove_subscription",
        description="Remove a user's subscription."
    )
    @app_commands.describe(user="The user whose subscription should be removed.")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_subscription(self, interaction: discord.Interaction, user: discord.User):
        try:
            result = await self.subscriptions.delete_one({"_id": int(user.id)})

            if result.deleted_count == 1:
                return await interaction.response.send_message(f"Subscription removed for {user.mention}.",
                                                               ephemeral=True)
            else:
                return await interaction.response.send_message(f"No subscription found for {user.mention}.",
                                                               ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to remove subscription for {user.id} | {user.name}: {e}")
            return await interaction.response.send_message("Failed to remove subscription. Please try again later.",
                                                           ephemeral=True)


async def setup(client):
    await client.add_cog(Subscription(client))
