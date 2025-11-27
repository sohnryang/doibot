import discord
from discord import app_commands
from discord.ext import commands


class Greet(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="greet", description="Greets the user!")
    async def greet(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Hello, {interaction.user.display_name}!"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Greet(bot))
