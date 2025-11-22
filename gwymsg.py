import discord
from discord.ext import commands
import asyncio

class GwyMsg(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Replace with your ticket category ID
    TICKET_CATEGORY_ID = 1386644137411088437

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if isinstance(channel, discord.TextChannel) and channel.category_id == self.TICKET_CATEGORY_ID:
            await asyncio.sleep(2)  # 2-second delay
            embed = discord.Embed(
                title="Giveaway Submission",
                description=(
                    "📩 Please send the following:\n\n"
                    "1. **Screenshot** of the giveaway & your win: ***"
                    "(showing message with your name)***\n\n"
                    "2. **Prize you won**, choose your prize: ***"
                    "(e.g., Nitro, Crypto, Custom items, etc.)***\n\n"
                    "3. **Time & Channel** of the giveaway: ***"
                    "(if possible)***"
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(
                text="Submitting fake or reused screenshots = warn + giveaway ban."
            )
            await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(GwyMsg(bot))