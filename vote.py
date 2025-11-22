import discord
from discord.ext import commands

VOTE_URL = "https://top.gg/bot/1423421449028239370/vote"

class Vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="vote")
    async def vote(self, ctx):
        """Send the vote link for Furina."""
        embed = discord.Embed(
            title="🗳️ Support Furina by Voting!",
            description=(
                "Voting helps **Furina** grow and reach more servers!\n"
                "You can vote every **12 hours** to show your support 💙\n\n"
                f"**[Click here to vote]({VOTE_URL})**"
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Vote(bot))