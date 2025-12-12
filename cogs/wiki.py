import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import math

USER_AGENT = "DiscordBot/1.0 (+https://discord.com)"
MAX_GALLERY = 3

class RelatedTopicButton(discord.ui.Button):
    def __init__(self, label: str, topic: str):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.topic = topic

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.view.cog.perform_search(interaction, self.topic)

class WikipediaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def perform_search(self, interaction: discord.Interaction, query: str):
        headers = {"User-Agent": USER_AGENT}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json"
                }
            ) as r:
                if r.status != 200:
                    return await interaction.followup.send(
                        f"Search failed (HTTP {r.status}).",
                        ephemeral=True
                    )
                try:
                    search_data = await r.json()
                except Exception:
                    return await interaction.followup.send(
                        "Wikipedia returned an invalid response.",
                        ephemeral=True
                    )

            results = search_data.get("query", {}).get("search", [])
            if not results:
                return await interaction.followup.send(
                    "No results found.",
                    ephemeral=True
                )

            page_title = results[0]["title"]

            async with session.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}"
            ) as r:
                if r.status != 200:
                    return await interaction.followup.send(
                        f"Summary lookup failed (HTTP {r.status}).",
                        ephemeral=True
                    )
                try:
                    summary = await r.json()
                except Exception:
                    return await interaction.followup.send(
                        "Invalid summary response.",
                        ephemeral=True
                    )

            async with session.get(
                f"https://en.wikipedia.org/api/rest_v1/page/media-list/{page_title}"
            ) as r:
                media_data = await r.json() if r.status == 200 else {}

        extract = summary.get("extract", "")
        short_desc = summary.get("description", "")
        page_url = summary.get("content_urls", {}).get("desktop", {}).get("page")
        thumbnail = summary.get("thumbnail", {}).get("source")
        lang = summary.get("lang", "N/A")
        page_type = summary.get("type", "unknown")

        words = len(extract.split()) if extract else 0
        read_time = max(1, math.ceil(words / 200)) if words else 0
        first_sentence = (extract.split(".")[0] + ".") if extract else ""

        images = []
        if "items" in media_data:
            for item in media_data["items"]:
                if item.get("type") == "image":
                    img = item.get("thumbnail", {}).get("src")
                    if img and img not in images:
                        images.append(img)
                if len(images) >= MAX_GALLERY:
                    break

        if thumbnail and thumbnail in images:
            images.remove(thumbnail)

        if page_type.lower() == "disambiguation":
            embed = discord.Embed(
                title=page_title,
                description=f"**{short_desc}**\n\n> {first_sentence or 'This page lists multiple topics.'}",
                color=discord.Color.blurple()
            )
            embed.set_footer(text="Last Updated: just now")

            embed.add_field(
                name="Useful Information",
                value=(
                    f"• Language: {lang.upper()}\n"
                    f"• Page Type: Disambiguation\n"
                    f"• Key Insight: {first_sentence or short_desc or 'Multiple topics share this title.'}"
                ),
                inline=False
            )

            view = discord.ui.View()
            view.cog = self

            for item in results[1:6]:
                topic = item.get("title")
                if topic:
                    view.add_item(RelatedTopicButton(label=topic, topic=topic))

            if page_url:
                view.add_item(discord.ui.Button(label="Open on Wikipedia", url=page_url))

            return await interaction.followup.send(embed=embed, view=view)

        embed = discord.Embed(
            title=page_title,
            description=(
                f"**{short_desc}**\n\n> {extract}"
                if extract else f"**{short_desc}**"
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Last Updated: just now")

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        useful_info_value = (
            f"• Language: {lang.upper()}\n"
            f"• Page Type: {page_type.capitalize()}\n"
        )
        if words:
            useful_info_value += (
                f"• Word Count: {words}\n"
                f"• Reading Time: ~{read_time} min\n"
            )
        if first_sentence:
            useful_info_value += f"• Key Insight: {first_sentence}"

        embed.add_field(
            name="Useful Information",
            value=useful_info_value,
            inline=False
        )

        if images:
            embed.add_field(name="Image Gallery", value="\u200b", inline=False)
            embed.set_image(url=images[0])

        view = discord.ui.View()
        view.cog = self

        if page_url:
            view.add_item(discord.ui.Button(label="Open on Wikipedia", url=page_url))

        for idx, img_url in enumerate(images[1:], start=2):
            view.add_item(discord.ui.Button(label=f"Image {idx}", url=img_url))

        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="search", description="Search Wikipedia and display info.")
    @app_commands.describe(query="The topic to search for.")
    async def search(self, interaction: discord.Interaction, query: str):
        if not interaction.response.is_done():
            await interaction.response.defer()
        await self.perform_search(interaction, query)

async def setup(bot):
    await bot.add_cog(WikipediaCog(bot))
