import discord
from discord.ext import commands
from datetime import datetime
from dateutil.relativedelta import relativedelta  # pip install python-dateutil


class AccAge(commands.Cog):
    """Shows the account age of a user."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="accage")
    async def accage(self, ctx, member: discord.Member = None):
        """Display the account creation date and age of a member."""
        member = member or ctx.author

        created = member.created_at.replace(tzinfo=None)
        now = datetime.utcnow()
        delta = relativedelta(now, created)

        embed = discord.Embed(
            title=f"Account Age — {member}",
            description=(
                f"**Created on:** {created.strftime('%d %B %Y at %H:%M:%S UTC')}\n\n"
                f"**Age:** `{delta.years} years, {delta.months} months, "
                f"{delta.days} days, {delta.hours} hours, "
                f"{delta.minutes} minutes, {delta.seconds} seconds`"
            ),
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AccAge(bot))
