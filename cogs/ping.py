import discord
from discord.ext import commands
import time


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", aliases=["latency"])
    async def ping(self, ctx: commands.Context):

        start = time.perf_counter()
        temp = await ctx.send("Measuring...")
        end = time.perf_counter()

        response_time = round((end - start) * 1000)
        latency = round(self.bot.latency * 1000)

        await temp.delete()

        view = discord.ui.LayoutView()

        container = discord.ui.Container(
            discord.ui.TextDisplay(
                f"## Pong!\n\n"
                f"WebSocket Latency: `{latency}ms`\n"
                f"Response Time: `{response_time}ms`"
            )
        )

        view.add_item(container)

        await ctx.send(view=view)


async def setup(bot):
    await bot.add_cog(Ping(bot))