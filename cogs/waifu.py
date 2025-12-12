import discord
from discord.ext import commands
import aiohttp
import random

class Waifu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_waifu(self, category: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.waifu.pics/sfw/{category}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("url")
                return None

    @commands.command(name="waifu")
    async def waifu(self, ctx, category: str = None):
        categories = ["waifu", "neko", "shinobu", "megumin"]

        if category is None or category.lower() not in categories:
            category = random.choice(categories)

        image_url = await self.fetch_waifu(category)

        if not image_url:
            return await ctx.send("Failed to fetch image.")

        embed = discord.Embed(
            title=f"Random {category.title()}",
            color=discord.Color.pink()
        )
        embed.set_image(url=image_url)
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )

        view = WaifuView(ctx, category, categories, self)
        await ctx.send(embed=embed, view=view)

class WaifuView(discord.ui.View):
    def __init__(self, ctx, category, categories, cog):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.category = category
        self.categories = categories
        self.cog = cog

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You cannot control this menu.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.green)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        image_url = await self.cog.fetch_waifu(self.category)

        embed = discord.Embed(
            title=f"Random {self.category.title()}",
            color=discord.Color.pink()
        )
        embed.set_image(url=image_url)
        embed.set_footer(
            text=f"Requested by {self.ctx.author.display_name}",
            icon_url=self.ctx.author.display_avatar.url
        )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Change Category", style=discord.ButtonStyle.blurple)
    async def change(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.category = random.choice(self.categories)
        image_url = await self.cog.fetch_waifu(self.category)

        embed = discord.Embed(
            title=f"Random {self.category.title()}",
            color=discord.Color.pink()
        )
        embed.set_image(url=image_url)
        embed.set_footer(
            text=f"Requested by {self.ctx.author.display_name}",
            icon_url=self.ctx.author.display_avatar.url
        )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

async def setup(bot):
    await bot.add_cog(Waifu(bot))
