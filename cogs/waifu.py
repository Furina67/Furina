import discord
from discord.ext import commands
import aiohttp


class Waifu(commands.Cog):
    CATEGORIES = ["waifu", "shinobu", "megumin"]

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    async def fetch_image(self, category: str):
        async with self.session.get(f"https://api.waifu.pics/sfw/{category}") as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get("url")

    def build_embed(self, image_url, category, author):
        embed = discord.Embed(
            title=f"Random {category.title()}",
            description=f"[Image link]({image_url})",
            color=discord.Color.pink(),
        )
        embed.set_image(url=image_url)
        embed.set_footer(
            text=f"Requested by {author.display_name}",
            icon_url=author.display_avatar.url,
        )
        return embed

    @commands.command(name="waifu")
    async def waifu(self, ctx: commands.Context):
        category_index = 0
        category = self.CATEGORIES[category_index]
        image_url = await self.fetch_image(category)

        if not image_url:
            return await ctx.send("Could not fetch a safe image.")

        embed = self.build_embed(image_url, category, ctx.author)
        await ctx.send(embed=embed, view=WaifuView(ctx, category_index, self))


class WaifuView(discord.ui.View):
    def __init__(self, ctx: commands.Context, category_index: int, cog: Waifu):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.category_index = category_index
        self.cog = cog

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "You can’t control this.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        category = self.cog.CATEGORIES[self.category_index]
        image_url = await self.cog.fetch_image(category)
        if not image_url:
            return

        embed = self.cog.build_embed(
            image_url,
            category,
            self.ctx.author,
        )
        await interaction.followup.edit_message(
            interaction.message.id,
            embed=embed,
            view=self,
        )

    @discord.ui.button(label="Change Category", style=discord.ButtonStyle.gray)
    async def change_category(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.defer()

        self.category_index = (self.category_index + 1) % len(self.cog.CATEGORIES)
        category = self.cog.CATEGORIES[self.category_index]
        image_url = await self.cog.fetch_image(category)
        if not image_url:
            return

        embed = self.cog.build_embed(
            image_url,
            category,
            self.ctx.author,
        )
        await interaction.followup.edit_message(
            interaction.message.id,
            embed=embed,
            view=self,
        )

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(Waifu(bot))