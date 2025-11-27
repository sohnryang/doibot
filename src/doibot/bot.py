import os
import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class MyBot(commands.Bot):
    def __init__(self):
        # Set intents for the bot.
        # discord.Intents.default() provides most common intents.
        # message_content intent is required for accessing message.content in most cases.
        # However, for slash commands, it might not be strictly necessary, but good practice for general bots.
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"), intents=intents
        )
        self.initial_extensions = ["doibot.commands.greet"]
        self.synced = False  # To check if commands have been synced

    async def setup_hook(self):
        # Load extensions (cogs)
        for extension in self.initial_extensions:
            await self.load_extension(extension)
        await self.tree.sync()
        self.synced = True

    async def on_ready(self):
        if not self.synced:
            await self.tree.sync()
            self.synced = True
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")


async def main():
    discord.utils.setup_logging()
    token = os.getenv("DISCORD_TOKEN")
    if token is None:
        logger.error("Error: DISCORD_TOKEN environment variable not set.")
        return

    bot = MyBot()
    await bot.start(token)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
