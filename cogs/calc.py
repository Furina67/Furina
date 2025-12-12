import discord
from discord.ext import commands
import math

class Calculator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="calc", aliases=["calculate"])
    async def calc(self, ctx, *, expression: str = None):
        if not expression:
            return await ctx.send("Please provide something to calculate.\nExample: `,calc 5+5*2`")

        allowed = "0123456789+-*/().% "
        if any(ch not in allowed for ch in expression):
            return await ctx.send("Invalid characters detected. Only use numbers and + - * / ( ) %")

        try:
            result = eval(expression, {"__builtins__": None}, math.__dict__)
        except Exception:
            return await ctx.send("Invalid equation!")

        embed = discord.Embed(
            description=f"{ctx.author.display_name}, the result is: **{result}**\nEquation: `{expression}`",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Calculator(bot))
