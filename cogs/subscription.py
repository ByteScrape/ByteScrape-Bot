import discord
from discord.ext import commands, tasks
from discord import ButtonStyle, app_commands
from discord.ui import Button, View
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils.config import Config
from utils.database import mongodb
from utils.embed import create_embed
from utils.logger import logger

config = Config()


def build_expired_embed(due_date: datetime, price: float, suspended: bool, message: str) -> discord.Embed:
    embed = create_embed(
        title="Subscription Expired",
        description=message,
        color=int(config.color, 16)
    )
    embed.add_field(name="Expiry Date:", value=f"<t:{int(due_date.timestamp())}:D>", inline=True)
    embed.add_field(name="Price:", value=f"{price}€", inline=True)
    embed.add_field(name="Payment Method:", value="PayPal", inline=True)
    embed.add_field(name="Service Suspended:", value=str(suspended), inline=True)
    return embed


def build_subscription_view() -> View:
    view = View()
    view.add_item(Button(label="Confirm Payment", style=ButtonStyle.green, custom_id="paid"))
    view.add_item(Button(label="Cancel Payment", style=ButtonStyle.red, custom_id="cancel"))
    view.add_item(Button(label="Paypal", style=ButtonStyle.url, url=config.paypal))
    return view


class Subscription(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        # Initialize the subscriptions collection from the connected database.
        self.subscriptions = mongodb.get_database("ByteScrape")["subscriptions"]
        self.check_subscriptions.start()

    def cog_unload(self) -> None:
        self.check_subscriptions.cancel()

    @tasks.loop(hours=int(config.subscription_delay))
    async def check_subscriptions(self) -> None:
        current_time = datetime.now()

        async for document in self.subscriptions.find({"next_payment": {"$lte": current_time}}):
            user_id = document.get("_id")
            due_date = document.get("next_payment")
            price = document.get("price")
            user = self.client.get_user(user_id)

            if user is None:
                continue

            days_overdue = (current_time - due_date).days

            # Prepare the embed message and view based on the overdue duration.
            if days_overdue == 7:
                message = (
                    "Please renew your subscription to continue enjoying our services, "
                    "your service will be **suspended tomorrow** if you do not pay."
                )
                embed = build_expired_embed(due_date, price, suspended=False, message=message)
            elif days_overdue > 7:
                message = (
                    "Please renew your subscription to continue enjoying our services, "
                    "your service will **now** be **suspended**."
                )
                embed = build_expired_embed(due_date, price, suspended=True, message=message)
            elif 0 < days_overdue < 7:
                message = (
                    "Please renew your subscription to continue enjoying our services, "
                    "your service will be **suspended** in **7 days**."
                )
                embed = build_expired_embed(due_date, price, suspended=False, message=message)
            else:
                # If not overdue or negative days, skip processing.
                continue

            view = build_subscription_view()

            try:
                await user.send(embed=embed, view=view)
            except Exception:
                logger.error(f"Failed to send subscription expired message to {user.id} | {user.name}")

    @check_subscriptions.before_loop
    async def before_check(self) -> None:
        await self.client.wait_until_ready()
        logger.debug("Subscription check task starting...")

    @app_commands.command(
        name="add_subscription",
        description="Add a user subscription with a specified price and payment interval in months."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_subscription(
            self,
            interaction: discord.Interaction,
            user: discord.User,
            price: float,
            interval: int
    ) -> None:
        now = datetime.now()
        next_payment = now + relativedelta(months=interval)
        subscription_doc = {
            "_id": int(user.id),
            "price": price,
            "interval": interval,
            "last_paid": now,
            "next_payment": next_payment,
            "overdue_run": False
        }

        try:
            await self.subscriptions.insert_one(subscription_doc)
        except Exception as e:
            logger.error(f"Failed to add subscription for {user.id} | {user.name}: {e}")
            return await interaction.response.send_message(
                "Failed to add subscription. Please try again later.",
                ephemeral=True
            )

        await interaction.response.send_message(
            f"Subscription added for {user.mention} with a price of {price:.2f}€ "
            f"and a payment interval of {interval} months.",
            ephemeral=True
        )

    @app_commands.command(
        name="set_last_paid",
        description="Set the last paid date for a user's subscription (DD-MM-YYYY)."
    )
    @app_commands.describe(
        user="The user whose subscription last paid date should be updated.",
        last_paid="The new last paid date (DD-MM-YYYY)."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_last_paid(self, interaction: discord.Interaction, user: discord.User, last_paid: str) -> None:
        try:
            last_paid_date = datetime.strptime(last_paid, "%d-%m-%Y")
        except ValueError:
            return await interaction.response.send_message(
                "Invalid date format. Use DD-MM-YYYY.",
                ephemeral=True
            )

        subscription_doc = await self.subscriptions.find_one({"_id": int(user.id)})
        if not subscription_doc:
            return await interaction.response.send_message(
                f"No subscription found for {user.mention}.",
                ephemeral=True
            )

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
            return await interaction.response.send_message(
                "Failed to update subscription. Please try again later.",
                ephemeral=True
            )

        await interaction.response.send_message(
            f"Last paid date for {user.mention} updated to {last_paid_date.strftime('%Y-%m-%d')}. "
            f"Next payment is due on {next_payment.strftime('%Y-%m-%d')}.",
            ephemeral=True
        )

    @app_commands.command(
        name="remove_subscription",
        description="Remove a user's subscription."
    )
    @app_commands.describe(
        user="The user whose subscription should be removed."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_subscription(self, interaction: discord.Interaction, user: discord.User) -> None:
        try:
            result = await self.subscriptions.delete_one({"_id": int(user.id)})
            if result.deleted_count == 1:
                message = f"Subscription removed for {user.mention}."
            else:
                message = f"No subscription found for {user.mention}."
            await interaction.response.send_message(message, ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to remove subscription for {user.id} | {user.name}: {e}")
            await interaction.response.send_message(
                "Failed to remove subscription. Please try again later.",
                ephemeral=True
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Subscription(client))
