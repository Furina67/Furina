import discord
from discord.ext import commands
import aiohttp
import random
import time


class FurinaView(discord.ui.LayoutView):
    def __init__(self, cog, ctx):
        super().__init__(timeout=300)
        self.cog = cog
        self.ctx = ctx
        self.cooldowns = {}

        self.container = discord.ui.Container(
            accent_color=discord.Color.blue()
        )

        self.container.add_item(
            discord.ui.TextDisplay("## Furina")
        )

        self.gallery = discord.ui.MediaGallery()
        self.container.add_item(self.gallery)

        self.container.add_item(discord.ui.Separator())

        self.container.add_item(
            discord.ui.TextDisplay(
                "Furina pics only for you..."
            )
        )

        self.add_item(self.container)

        row = discord.ui.ActionRow()

        next_button = discord.ui.Button(
            label="Next",
            style=discord.ButtonStyle.primary,
            custom_id="furina_next"
        )

        next_button.callback = self.next_image
        row.add_item(next_button)

        self.add_item(row)

    async def next_image(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                "Only the command user can use this button.",
                ephemeral=True
            )

        now = time.time()
        last = self.cooldowns.get(interaction.user.id, 0)

        if now - last < 3:
            return await interaction.response.send_message(
                "Slow down.",
                ephemeral=True
            )

        self.cooldowns[interaction.user.id] = now

        post = await self.cog.get_image()
        if not post:
            return await interaction.response.send_message(
                "No images available.",
                ephemeral=True
            )

        image_url = post["file_url"]

        self.gallery.items = []
        self.gallery.add_item(media=image_url)

        await interaction.response.edit_message(view=self)


class Furina(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = []
        self.last_fetch = 0

    async def fetch_posts(self):
        url = "https://safebooru.org/index.php"

        params = {
            "page": "dapi",
            "s": "post",
            "q": "index",
            "json": 1,
            "limit": 100,
            "pid": random.randint(0, 50),
            "tags": "furina_(genshin_impact)"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print("Safebooru error:", resp.status)
                    return None

                try:
                    return await resp.json(content_type=None)
                except:
                    return None

    async def refresh_cache(self):
        for _ in range(5):
            data = await self.fetch_posts()
            if not data:
                continue

            clean = [
                p for p in data
                if p.get("file_url")
                and p["file_url"].startswith("http")
            ]

            if clean:
                random.shuffle(clean)
                self.cache = clean
                self.last_fetch = time.time()
                return True

        return False

    async def get_image(self):
        if not self.cache or time.time() - self.last_fetch > 600:
            success = await self.refresh_cache()
            if not success:
                return None

        if not self.cache:
            return None

        return self.cache.pop()

    @commands.command()
    async def furina(self, ctx):
        post = await self.get_image()
        if not post:
            return await ctx.send("No images found.")

        view = FurinaView(self, ctx)

        view.gallery.add_item(media=post["file_url"])

        await ctx.send(view=view)


async def setup(bot):
    await bot.add_cog(Furina(bot))