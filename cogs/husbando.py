import discord
from discord.ext import commands
import aiohttp

class Husbando(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_husbando(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://nekos.best/api/v2/husbando") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "results" in data:
                        r = data["results"][0]
                        return {
                            "url": r["url"],
                            "anime_name": r.get("anime_name", "Unknown"),
                            "artist_name": r.get("artist_name", "Unknown")
                        }

        return {
            "url": "https://nekos.best/api/v2/husbando/001.png",
            "anime_name": "Mystery Husbando",
            "artist_name": "Unknown"
        }

    @commands.command(name="husbando")
    async def husbando(self, ctx):
        data = await self.fetch_husbando()
        embed = discord.Embed(
            title="💙 Random Husbando",
            description=(
                f"🎬 **Anime/Game:** {data['anime_name']}\n"
                f"🎨 **Artist:** {data['artist_name']}"
            ),
            color=discord.Color.blue()
        )
        embed.set_image(url=data["url"])
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed, view=HusbandoView(ctx, self))


class HusbandoView(discord.ui.View):
    def __init__(self, ctx, cog):
        super().__init__(timeout=1200)
        self.ctx = ctx
        self.cog = cog

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You can’t control this.", ephemeral=True)
            return False
        return True

    async def update_embed(self, interaction, title):
        data = await self.cog.fetch_husbando()
        embed = discord.Embed(
            title=title,
            description=(
                f"🎬 **Anime/Game:** {data['anime_name']}\n"
                f"🎨 **Artist:** {data['artist_name']}"
            ),
            color=discord.Color.blurple()
        )
        embed.set_image(url=data["url"])
        embed.set_footer(text=f"Requested by {self.ctx.author.display_name}", icon_url=self.ctx.author.display_avatar.url)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.green)
    async def refresh(self, interaction, button):
        await self.update_embed(interaction, "💙 Random Husbando")

    @discord.ui.button(label="Next Husbando", style=discord.ButtonStyle.blurple)
    async def next_husbando(self, interaction, button):
        await self.update_embed(interaction, "💙 Next Husbando")

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, interaction, button):
        await interaction.message.delete()


async def setup(bot):
    await bot.add_cog(Husbando(bot))
