import discord
from discord.ext import commands
import secrets
import asyncio

class Coinflip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="coinflip", aliases=["cf"])
    async def coinflip(self, ctx, guess: str = None):
        sides = ["heads", "tails"]
        result = secrets.choice(sides)

        if guess and guess.lower() not in sides:
            return await ctx.send("Please choose either `heads` or `tails`.")

        flipping = discord.Embed(
            title="Flipping the coin...",
            color=discord.Color.blurple()
        )
        flipping.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        msg = await ctx.send(embed=flipping)
        await asyncio.sleep(2)

        if result == "heads":
            color = discord.Color.green()
        else:
            color = discord.Color.gold()

        description = f"{ctx.author.display_name} flipped a coin and got **{result.title()}**."

        if guess:
            if guess.lower() == result:
                description += "\nYou guessed correctly!"
                color = discord.Color.green()
            else:
                description += "\nYou guessed wrong!"
                color = discord.Color.red()

        embed = discord.Embed(
            title="Coinflip Result",
            description=description,
            color=color
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        await msg.edit(embed=embed)


async def setup(bot):
    await bot.add_cog(Coinflip(bot))
