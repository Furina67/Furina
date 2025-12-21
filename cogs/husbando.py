import discord
from discord.ext import commands
import aiohttp
import random
import urllib.parse


class Husbando(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    async def _from_nekos_best(self):
        async with self.session.get("https://nekos.best/api/v2/husbando") as resp:
            if resp.status != 200:
                return None

            data = await resp.json()
            r = data["results"][0]

            return {
                "url": r["url"],
                "anime_name": r.get("anime_name"),
                "artist_name": r.get("artist_name"),
            }

    async def _from_picre(self):
        tags = "1boy,male,solo"
        url = f"https://api.pic.re/image.json?tags={urllib.parse.quote(tags)}"

        async with self.session.get(url) as resp:
            if resp.status != 200:
                return None

            data = await resp.json()

            return {
                "url": data["file_url"],
                "anime_name": None,
                "artist_name": data.get("artist"),
            }

    async def fetch_husbando(self):
        sources = [
            self._from_nekos_best,
            self._from_picre,
        ]

        random.shuffle(sources)

        for source in sources:
            try:
                result = await source()
                if result and result.get("url"):
                    return result
            except Exception:
                continue

        return {
            "url": "https://i.imgur.com/8Km9tLL.png",
            "anime_name": None,
            "artist_name": None,
        }

    def build_embed(self, data, author):
        lines = []

        if data.get("anime_name"):
            lines.append(f"**Anime/Game:** {data['anime_name']}")

        if data.get("artist_name"):
            lines.append(f"**Artist:** {data['artist_name']}")

        if data.get("url"):
            lines.append(f"[Image link]({data['url']})")

        embed = discord.Embed(
            title="Random Husbando",
            description="\n".join(lines) or "No additional information available.",
            color=discord.Color.blue(),
        )

        embed.set_image(url=data["url"])
        embed.set_footer(
            text=f"Requested by {author.display_name}",
            icon_url=author.display_avatar.url,
        )
        return embed

    @commands.command(name="husbando")
    async def husbando(self, ctx: commands.Context):
        data = await self.fetch_husbando()
        embed = self.build_embed(data, ctx.author)
        await ctx.send(embed=embed, view=HusbandoView(ctx, self))


class HusbandoView(discord.ui.View):
    def __init__(self, ctx: commands.Context, cog: Husbando):
        super().__init__(timeout=1200)
        self.ctx = ctx
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
    async def next_husbando(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = await self.cog.fetch_husbando()
        embed = self.cog.build_embed(data, self.ctx.author)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(Husbando(bot))