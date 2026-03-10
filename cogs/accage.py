import discord
from discord.ext import commands
from datetime import datetime
from dateutil.relativedelta import relativedelta


def format_duration(delta: relativedelta) -> str:
    parts = []

    if delta.years:
        parts.append(f"{delta.years} year{'s' if delta.years != 1 else ''}")
    if delta.months:
        parts.append(f"{delta.months} month{'s' if delta.months != 1 else ''}")
    if delta.days:
        parts.append(f"{delta.days} day{'s' if delta.days != 1 else ''}")
    if delta.hours:
        parts.append(f"{delta.hours} hour{'s' if delta.hours != 1 else ''}")
    if delta.minutes:
        parts.append(f"{delta.minutes} minute{'s' if delta.minutes != 1 else ''}")
    if delta.seconds or not parts:
        parts.append(f"{delta.seconds} second{'s' if delta.seconds != 1 else ''}")

    return ", ".join(parts)


class AccAgeView(discord.ui.LayoutView):
    def __init__(self, user: discord.User, member: discord.Member | None):
        super().__init__(timeout=None)

        now = datetime.utcnow()

        created = user.created_at.replace(tzinfo=None)
        acc_delta = relativedelta(now, created)

        created_text = created.strftime("%d %B %Y â€¢ %H:%M:%S")
        acc_age = format_duration(acc_delta)

        if member and member.joined_at:
            joined = member.joined_at.replace(tzinfo=None)
            join_delta = relativedelta(now, joined)
            joined_text = joined.strftime("%d %B %Y â€¢ %H:%M:%S")
            join_age = format_duration(join_delta)
        else:
            joined_text = "Not available"
            join_age = "Not available"

        container = discord.ui.Container()

        container.add_item(
            discord.ui.Section(
                discord.ui.TextDisplay(
                    f"## {user.name}\n"
                    f"Created: {created_text}\n"
                    f"Age: {acc_age}\n\n"
                    f"Joined: {joined_text}\n"
                    f"In Server For: {join_age}"
                ),
                accessory=discord.ui.Thumbnail(user.display_avatar.url)
            )
        )

        self.add_item(container)


class AccAge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="accage",
        description="Shows account age and server join age"
    )
    async def accage(self, ctx: commands.Context, user: discord.User | None = None):
        user = user or ctx.author
        member = ctx.guild.get_member(user.id) if ctx.guild else None

        view = AccAgeView(user, member)

        if ctx.interaction:
            await ctx.interaction.response.send_message(view=view)
        else:
            await ctx.send(view=view)


async def setup(bot):
    await bot.add_cog(AccAge(bot))