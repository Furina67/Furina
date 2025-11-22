# cogs/accage.py

import discord

from discord.ext import commands

from datetime import datetime

from dateutil.relativedelta import relativedelta  # pip install python-dateutil

class AccAge(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    @commands.command(name="accage")

    async def accage(self, ctx, member: discord.Member = None):

        """Show the account age of a user."""

        member = member or ctx.author

        created = member.created_at.replace(tzinfo=None)

        now = datetime.utcnow()

        delta = relativedelta(now, created)

        years = delta.years

        months = delta.months

        days = delta.days

        hours = delta.hours

        minutes = delta.minutes

        seconds = delta.seconds

        embed = discord.Embed(

            title=f"<:1000033535:1433229292564906004> Account Age of {member.name}",

            description=(

                f"<a:1000033534:1433228352512065606> **Created on:** {created.strftime('%d %B %Y at %H:%M:%S UTC')}\n\n"

                f"<a:1000033534:1433228352512065606> **Age:** `{years} years, {months} months, {days} days, "

                f"{hours} hours, {minutes} minutes, {seconds} seconds`"

            ),

            color=discord.Color.blurple()

        )

        embed.set_thumbnail(url=member.display_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):

    await bot.add_cog(AccAge(bot))