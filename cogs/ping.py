import discord
from discord.ext import commands
import time

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", aliases=["latency"])
    async def ping(self, ctx):
        start = time.perf_counter()
        msg = await ctx.send("🏓 Pinging...")
        end = time.perf_counter()

        ws_latency = round(self.bot.latency * 1000)
        response_time = round((end - start) * 1000)

        if ws_latency < 100:
            color = discord.Color.green()
        elif ws_latency < 200:
            color = discord.Color.yellow()
        else:
            color = discord.Color.red()

        embed = discord.Embed(title="🏓 Pong!", color=color)
        embed.add_field(name="📡 WebSocket Latency", value=f"**{ws_latency}ms**", inline=False)
        embed.add_field(name="⌛ Response Time", value=f"**{response_time}ms**", inline=False)
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )

        await msg.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(Ping(bot))
