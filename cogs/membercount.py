import discord
from discord.ext import commands


class MemberCountView(discord.ui.LayoutView):
    def __init__(self, guild: discord.Guild):
        super().__init__()

        total = guild.member_count or 0
        humans = len([m for m in guild.members if not m.bot])
        bots = total - humans
        online = len([m for m in guild.members if m.status != discord.Status.offline])

        human_percent = round((humans / total) * 100, 1) if total else 0
        bot_percent = round((bots / total) * 100, 1) if total else 0

        section = discord.ui.Section(
            f"## Member Count for {guild.name}\n\n"
            f"<:Users:1479937107639144528> Total Members: {total}\n"
            f"<:Member:1479937110327820532> Humans: {humans} ({human_percent}%)\n"
            f"<:Bots:1479937113603702886> Bots: {bots} ({bot_percent}%)\n"
            f"<:1000033596:1433522455359782912> Online: {online}",
            accessory=discord.ui.Thumbnail(
                guild.icon.url if guild.icon else None
            )
        )

        container = discord.ui.Container()
        container.add_item(section)

        self.add_item(container)


class MemberCount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="membercount",
        description="Shows total server members and statistics", aliases=["members", "count", "mc"]
    )
    async def membercount(self, ctx: commands.Context):
        view = MemberCountView(ctx.guild)
        await ctx.send(view=view)


async def setup(bot):
    await bot.add_cog(MemberCount(bot))