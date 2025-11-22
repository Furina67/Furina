import discord

from discord.ext import commands

import aiohttp

import random

class Husbando(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    async def fetch_husbando(self):

        """Fetch husbando image and info"""

        # nekos.best provides good husbando data (image + anime name)

        async with aiohttp.ClientSession() as session:

            async with session.get("https://nekos.best/api/v2/husbando") as resp:

                if resp.status == 200:

                    data = await resp.json()

                    if "results" in data:

                        result = data["results"][0]

                        return {

                            "url": result["url"],

                            "anime_name": result.get("anime_name", "Unknown"),

                            "artist_name": result.get("artist_name", "Unknown")

                        }

        # fallback if API fails

        return {

            "url": "https://cdn.waifu.pics/sfw/waifu",

            "anime_name": "Mystery Husbando",

            "artist_name": "Unknown"

        }

    @commands.command(name="husbando")

    async def husbando(self, ctx):

        """Send a random husbando image + info with buttons"""

        husbando = await self.fetch_husbando()

        embed = discord.Embed(

            title="💙 Random Husbando",

            description=f"🎬 **Anime/Game:** {husbando['anime_name']}\n🎨 **Artist:** {husbando['artist_name']}",

            color=discord.Color.blue()

        )

        embed.set_image(url=husbando["url"])

        embed.set_footer(

            text=f"Requested by {ctx.author.display_name}",

            icon_url=ctx.author.display_avatar.url

        )

        await ctx.send(embed=embed, view=HusbandoView(ctx, self))

class HusbandoView(discord.ui.View):

    def __init__(self, ctx, cog):

        super().__init__(timeout=1200)  # 20 minutes

        self.ctx = ctx

        self.cog = cog

    async def interaction_check(self, interaction: discord.Interaction):

        if interaction.user != self.ctx.author:

            await interaction.response.send_message("❌ You can’t control this!", ephemeral=True)

            return False

        return True

    @discord.ui.button(label="🔁 Refresh", style=discord.ButtonStyle.green)

    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):

        husbando = await self.cog.fetch_husbando()

        embed = discord.Embed(

            title="💙 Random Husbando",

            description=f"🎬 **Anime:** {husbando['anime_name']}\n🎨 **Artist:** {husbando['artist_name']}",

            color=discord.Color.blue()

        )

        embed.set_image(url=husbando["url"])

        embed.set_footer(

            text=f"Requested by {self.ctx.author.display_name}",

            icon_url=self.ctx.author.display_avatar.url

        )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="➡️ Next Husbando", style=discord.ButtonStyle.blurple)

    async def next_husbando(self, interaction: discord.Interaction, button: discord.ui.Button):

        husbando = await self.cog.fetch_husbando()

        embed = discord.Embed(

            title="💙 Next Husbando",

            description=f"🎬 **Anime/Game:** {husbando['anime_name']}\n🎨 **Artist:** {husbando['artist_name']}",

            color=discord.Color.blurple()

        )

        embed.set_image(url=husbando["url"])

        embed.set_footer(

            text=f"Requested by {self.ctx.author.display_name}",

            icon_url=self.ctx.author.display_avatar.url

        )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.red)

    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.message.delete()

async def setup(bot):
    await bot.add_cog(Husbando(bot))