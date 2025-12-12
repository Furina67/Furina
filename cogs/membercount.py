import discord
from discord.ext import commands

class MemberCount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="membercount", aliases=["members", "count", "mc"])
    async def membercount(self, ctx):
        guild = ctx.guild
        total = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])

        embed = discord.Embed(
            title=f"Member Count — {guild.name}",
            description=(
                f"**Total Members:** `{total}`\n"
                f"**Humans:** `{humans}`\n"
                f"**Bots:** `{bots}`"
            ),
            color=discord.Color.blue()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MemberCount(bot))
