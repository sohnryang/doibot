import logging
import os
import urllib.parse

import discord
import requests
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class DoiPreview(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.crossref_api_base = os.getenv("CROSSREF_API", "https://api.crossref.org")

    @app_commands.command(name="doi", description="Preview a DOI link.")
    async def doi_preview(self, interaction: discord.Interaction, doi_input: str):
        await interaction.response.defer(thinking=True)

        doi = doi_input
        if doi_input.startswith(("http://", "https://")):
            parsed_url = urllib.parse.urlparse(doi_input)
            if parsed_url.netloc == "doi.org" or parsed_url.netloc.endswith(".doi.org"):
                # Extract the path and remove leading '/'
                doi = parsed_url.path.lstrip("/")
            else:
                await interaction.followup.send(
                    f"The provided link `{doi_input}` does not appear to be a DOI.org link."
                )
                return

        url = f"{self.crossref_api_base}/works/{doi}"

        try:
            # Run the blocking requests.get in a separate thread to avoid blocking the event loop
            response = await self.bot.loop.run_in_executor(None, requests.get, url)

            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})

                title = (
                    message.get("title", ["N/A"])[0] if message.get("title") else "N/A"
                )

                container_title = "N/A"
                if message.get("container-title"):
                    container_title = message["container-title"][0]
                elif message.get("event"):  # Conference
                    container_title = (
                        message["event"]["name"]
                        if isinstance(message["event"], dict)
                        and "name" in message["event"]
                        else message["event"]
                    )
                elif message.get("publisher"):
                    container_title = message["publisher"]

                published_year = "N/A"
                if "published-print" in message and message["published-print"].get(
                    "date-parts"
                ):
                    published_year = message["published-print"]["date-parts"][0][0]
                elif "published-online" in message and message["published-online"].get(
                    "date-parts"
                ):
                    published_year = message["published-online"]["date-parts"][0][0]
                elif "created" in message and message["created"].get("date-parts"):
                    published_year = message["created"]["date-parts"][0][0]

                authors = "N/A"
                if message.get("author"):
                    author_list = []
                    for author in message["author"]:
                        name_parts = []
                        if author.get("given"):
                            name_parts.append(author["given"])
                        if author.get("family"):
                            name_parts.append(author["family"])
                        if name_parts:
                            author_list.append(" ".join(name_parts))
                    authors = ", ".join(author_list) if author_list else "N/A"

                abstract = message.get("abstract", "No abstract available.")
                if abstract.startswith("<jats:p>"):  # Remove JATS XML tags if present
                    abstract = abstract.replace("<jats:p>", "").replace("</jats:p>", "")

                # Truncation logic
                TRUNCATE_LIMIT = 300
                description = abstract

                if len(abstract) > TRUNCATE_LIMIT:
                    description = abstract[:TRUNCATE_LIMIT].rsplit(" ", 1)[0] + "..."

                embed = discord.Embed(
                    title=title,
                    url=f"https://doi.org/{doi}",
                    description=description,
                    color=discord.Color.blue(),
                )
                embed.add_field(name="Authors", value=authors, inline=False)
                embed.add_field(
                    name="Journal/Conference", value=container_title, inline=True
                )
                embed.add_field(
                    name="Published Year", value=published_year, inline=True
                )
                embed.set_footer(text=f"DOI: {doi}")

                await interaction.followup.send(embed=embed)

            elif response.status_code == 404:
                await interaction.followup.send(
                    f"Could not find information for DOI: `{doi}`. It might be invalid."
                )
            else:
                await interaction.followup.send(
                    f"An error occurred while fetching DOI information (Status: {response.status_code})."
                )
                logger.error(
                    f"Crossref API error for DOI {doi}: {response.status_code} - {response.text}"
                )

        except requests.exceptions.RequestException as e:
            await interaction.followup.send(
                "Could not connect to the Crossref API. Please try again later."
            )
            logger.error(f"Requests exception for DOI {doi}: {e}")
        except Exception as e:
            await interaction.followup.send(
                "An unexpected error occurred while processing your request."
            )
            logger.error(f"Unexpected error for DOI {doi}: {e}", exc_info=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(DoiPreview(bot))
