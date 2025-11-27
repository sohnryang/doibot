import asyncio

from src.doibot.bot import main as bot_main


def main() -> None:
    asyncio.run(bot_main())
