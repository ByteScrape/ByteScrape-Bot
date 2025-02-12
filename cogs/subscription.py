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


def create_embeds(description: str, title: str) -> list[discord.Embed]:
    embeds = []
    description_limit = 2700  # maximum characters allowed in the description
    current_embed = discord.Embed(
        color=int(config.color, 16),
        title=title
    )
    # Split description lines to try preserving formatting
    remaining_lines = description.splitlines()
    current_description = ""

    while remaining_lines:
        next_line = remaining_lines[0]
        # Check if we can add this line without exceeding the limit
        if len(current_description) + len(next_line) + 1 <= description_limit:
            current_description += next_line + "\n"
            remaining_lines.pop(0)
        else:
            current_embed.description = current_description
            embeds.append(current_embed)
            # Create a new embed with the same style
            current_embed = discord.Embed(color=int(config.color, 16))
            current_description = ""

    # Append final embed if there's any content left
    if current_description:
        current_embed.description = current_description
        current_embed.timestamp = datetime.now()
        current_embed.set_footer(text=config.footer_text, icon_url=config.footer_icon)
        embeds.append(current_embed)

    return embeds

def build_expired_embed(due_date: datetime, price: float, suspended: bool, message: str, user: discord.User) -> discord.Embed:
    embed = create_embed(
        title=f"Subscription Expired",
        description=message,
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
                    f"{user.mention}\n"
                    "Please renew your subscription to continue enjoying our services, "
                    "your service will be **suspended tomorrow** if you do not pay."
                )
                embed = build_expired_embed(due_date, price, suspended=False, message=message, user=user)
            elif days_overdue > 7:
                message = (
                    f"{user.mention}\n"
                    "Please renew your subscription to continue enjoying our services, "
                    "your service will **now** be **suspended**."
                )
                embed = build_expired_embed(due_date, price, suspended=False, message=message, user=user)
            elif 0 < days_overdue < 7:
                message = (
                    f"{user.mention}\n"
                    "Please renew your subscription to continue enjoying our services, "
                    "your service will be **suspended** in **7 days**."
                )
                embed = build_expired_embed(due_date, price, suspended=False, message=message, user=user)
            else:
                # If not overdue or negative days, skip processing.
                continue

            view = build_subscription_view()

            try:
                await user.send(embed=embed, view=view)
                channel = self.client.get_channel(int(config.subscriptions_id))
                if channel:
                    await channel.send(embed=embed)

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
            interval: int,
            email: str = None,
    ) -> None:
        now = datetime.now()
        next_payment = now + relativedelta(months=interval)
        subscription_doc = {
            "_id": int(user.id),
            "price": price,
            "interval": interval,
            "last_paid": now,
            "next_payment": next_payment,
            "overdue_run": False,
            "email": email
        }

        try:
            await self.subscriptions.insert_one(subscription_doc)
        except Exception as e:
            logger.error(f"Failed to add subscription for {user.id} | {user.name}: {e}")
            return await interaction.response.send_message(
                "Failed to add subscription. Please try again later.",
                ephemeral=True
            )

        try:
            await user.send(
                f"You have been **subscribed** to the **ByteScrape** service for **{interval} months**. "
                f"Your subscription will be **renewed** on **{next_payment.strftime('%Y-%m-%d')}**. "
                f"Please **pay** your **subscription** till 7 days after due date. If not your service will be **suspended**."
            )
        except Exception:
            logger.error(f"Failed to send subscription message to {user.id} | {user.name}")

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

    @app_commands.command(
        name="list_subscriptions",
        description="List all subscriptions from the database."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def list_subscriptions(self, interaction: discord.Interaction) -> None:
        db = mongodb.get_database("ByteScrape")
        subs_collection = db["subscriptions"]

        # Retrieve subscriptions (limit to 100 for this example)
        subscriptions = await subs_collection.find({}).to_list(length=100)

        if not subscriptions:
            await interaction.response.send_message("No subscriptions found.", ephemeral=True)
            return

        # Create a numbered list with all subscription information
        lines = []
        for index, doc in enumerate(subscriptions, start=1):
            user_id = doc.get("_id", "Unknown")
            last_paid = doc.get("last_paid")
            next_payment = doc.get("next_payment")
            interval = doc.get("interval", "N/A")  # interval in months

            if isinstance(last_paid, datetime):
                last_paid = last_paid.strftime("%Y-%m-%d")
            else:
                last_paid = str(last_paid) if last_paid else "N/A"

            if isinstance(next_payment, datetime):
                next_payment = next_payment.strftime("%Y-%m-%d")
            else:
                next_payment = str(next_payment) if next_payment else "N/A"

            lines.append(
                f"{index}) User: <@{user_id}> | Last Paid: {last_paid} | Next Payment: {next_payment} | Interval: {interval} month(s)"
            )

        full_description = "\n".join(lines)
        # Split the long description into multiple embeds, if necessary
        embeds = create_embeds(full_description, title="Subscriptions List")

        # Send the first embed as the initial response, then follow up with the rest if there are any
        await interaction.response.send_message(embed=embeds[0], ephemeral=True)
        if len(embeds) > 1:
            for embed in embeds[1:]:
                await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Subscription(client))
