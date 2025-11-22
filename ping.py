import discord
from discord.ext import commands
import time

class Ping(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    @commands.command(name="ping", aliases=["latency"])

    async def ping(self, ctx):

        """Shows the bot latency."""

        start = time.perf_counter()

        message = await ctx.send("🏓 Pinging...")

        end = time.perf_counter()

        latency = round(self.bot.latency * 1000)       # Gateway latency

        response_time = round((end - start) * 1000)    # Message round-trip

        # Choose color by latency

        if latency < 100:

            color = discord.Color.green()

        elif latency < 200:

            color = discord.Color.yellow()

        else:

            color = discord.Color.red()

        embed = discord.Embed(

            title="🏓 Pong!",

            color=color

        )

        embed.add_field(name="📡 WebSocket Latency", value=f"**{latency}ms**", inline=False)

        embed.add_field(name="⌛ Response Time", value=f"**{response_time}ms**", inline=False)

        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        await message.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(Ping(bot))