import discord

from discord.ext import commands

import secrets

import asyncio

class Coinflip(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    @commands.command(name="coinflip", aliases=["cf"])

    async def coinflip(self, ctx, guess: str = None):

        """

        Flip a coin! Optionally guess heads or tails.

        Example: ,cf heads

        """

        sides = ["heads", "tails"]

        result = secrets.choice(sides)

        # Validate guess if provided

        if guess and guess.lower() not in sides:

            return await ctx.send("❌ Please choose either `heads` or `tails`!")

        # Initial embed (flipping animation)

        flipping = discord.Embed(

            title="🪙 Flipping the coin...",

            color=discord.Color.blurple()

        )

        flipping.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        msg = await ctx.send(embed=flipping)

        await asyncio.sleep(2)  # suspense 😏

        # Final result

        if result == "heads":

            emoji = "<:1000033531:1433206847157833788>"

            color = discord.Color.green()

        else:

            emoji = "<:1000033532:1433206849368227951>"

            color = discord.Color.gold()

        description = f"**{ctx.author.display_name}** flipped a coin and got **{result.title()}!** {emoji}"

        # Check guess

        if guess:

            if guess.lower() == result:

                description += "\n<:1000033529:1433199457624784947> You guessed **correctly!**"

                color = discord.Color.green()

            else:

                description += "\n<:1000033528:1433199141395370145> You guessed **wrong!**"

                color = discord.Color.red()

        embed = discord.Embed(

            title="🪙 Coinflip Result",

            description=description,

            color=color

        )

        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        await msg.edit(embed=embed)

async def setup(bot):

    await bot.add_cog(Coinflip(bot))