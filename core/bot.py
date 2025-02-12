from pathlib import Path

import discord
from discord.ext import commands

from utils.database import mongodb
from utils.logger import logger
from utils.config import Config


class Bot(commands.Bot):
    def __init__(self):
        allowed_mentions = discord.AllowedMentions(everyone=False, users=True, roles=True)
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=".",
            intents=intents,
            allowed_mentions=allowed_mentions,
            description=Config().description,
            heartbeat_timeout=150.0,
            chunk_guilds_at_startup=False,
            case_insensitive=True,
        )
        self.logger = logger
        self.config = Config()
        self.synced = False

    async def setup_hook(self):
        await mongodb.connect()


    async def on_ready(self):
        await self.wait_until_ready()
        await self.load_cogs()
        await self.change_presence(
            activity=discord.Game(name=self.config.activity),
            status=self.get_status()
        )
        if not self.synced:
            await self.tree.sync()
            self.synced = True
        self.logger.debug("Bot started", extra={"emoji": ":bomb:"})

    def get_status(self):
        try:
            status = int(self.config.status)
        except ValueError:
            status = 0
        status_mapping = {
            0: discord.Status.online,
            1: discord.Status.idle,
            2: discord.Status.dnd,
            3: discord.Status.invisible,
        }
        return status_mapping.get(status, discord.Status.online)

    async def load_cogs(self):
        cogs_path = Path("cogs")
        if not cogs_path.is_dir():
            return
        for cog_file in cogs_path.glob("*.py"):
            try:
                await self.load_extension(f"cogs.{cog_file.stem}")
            except Exception as e:
                self.logger.error(
                    f"Could not load extension {cog_file.stem}: {e}",
                    extra={"emoji": ":stop_sign:"}
                )

    def run(self):
        self.logger.debug("Starting...", extra={"emoji": ":bomb:"})
        try:
            super().run(self.config.token, reconnect=True)
        except Exception as e:
            self.logger.critical(f"Bot failed to start: {e}", extra={"emoji": ":warning:"})
