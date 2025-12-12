import discord
from discord.ext import commands
import asyncio
import datetime
import platform
import psutil


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = {}

    @commands.command(name="userinfo")
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        embed = discord.Embed(
            title=f"User Information — {member}",
            color=discord.Color.blue()
        )

        embed.set_thumbnail(
            url=member.avatar.url if member.avatar else member.default_avatar.url
        )

        embed.add_field(
            name="Basic Info",
            value=(
                f"User: {member.mention}\n"
                f"ID: `{member.id}`\n"
                f"Bot: `{member.bot}`\n"
                f"Status: `{member.status}`"
            ),
            inline=False
        )

        embed.add_field(
            name="Server Info",
            value=(
                f"Top Role: {member.top_role.mention}\n"
                f"Roles: {len(member.roles) - 1}"
            ),
            inline=False
        )

        embed.add_field(
            name="Timestamps",
            value=(
                f"Joined Server: <t:{int(member.joined_at.timestamp())}:f> "
                f"(<t:{int(member.joined_at.timestamp())}:R>)\n"
                f"Account Created: <t:{int(member.created_at.timestamp())}:f> "
                f"(<t:{int(member.created_at.timestamp())}:R>)"
            ),
            inline=False
        )

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="roleinfo")
    async def roleinfo(self, ctx, *, role: discord.Role):
        perms = [
            perm.replace("_", " ").title()
            for perm, value in role.permissions
            if value
        ]
        permissions = ", ".join(perms) if perms else "No permissions"

        embed = discord.Embed(
            title=f"Role Information — {role.name}",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Basic Info",
            value=(
                f"ID: `{role.id}`\n"
                f"Color: `{role.color}`\n"
                f"Mentionable: `{role.mentionable}`\n"
                f"Hoisted: `{role.hoist}`\n"
                f"Members: `{len(role.members)}`"
            ),
            inline=False
        )

        embed.add_field(
            name="Permissions",
            value=permissions,
            inline=False
        )

        embed.add_field(
            name="Created At",
            value=(
                f"<t:{int(role.created_at.timestamp())}:f> "
                f"(<t:{int(role.created_at.timestamp())}:R>)"
            ),
            inline=False
        )

        if role.icon:
            embed.set_thumbnail(url=role.icon.url)
        else:
            embed.set_thumbnail(
                url=f"https://singlecolorimage.com/get/{str(role.color).replace('#', '')}/100x100"
            )

        embed.set_footer(
            text=f"Requested by {ctx.author}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="botinfo")
    async def botinfo(self, ctx):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        uptime = (
            datetime.datetime.utcnow() - self.bot.launch_time
            if hasattr(self.bot, "launch_time")
            else "Unknown"
        )

        embed = discord.Embed(
            title="Bot Information",
            color=discord.Color.blue()
        )

        embed.set_thumbnail(
            url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None
        )

        embed.add_field(name="Developer", value="832459817485860894", inline=True)
        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        embed.add_field(name="discord.py Version", value=discord.__version__, inline=True)
        embed.add_field(name="CPU Usage", value=f"{cpu}%", inline=True)
        embed.add_field(name="Memory Usage", value=f"{mem}%", inline=True)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(
            name="Latency",
            value=f"{round(self.bot.latency * 1000)}ms",
            inline=True
        )

        embed.set_footer(text=f"Uptime: {uptime}")

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="invite")
    async def invite(self, ctx):
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=discord.Permissions.all()
        )

        embed = discord.Embed(
            title="Invite Me",
            description=f"[Click here to invite me]({invite_url})",
            color=discord.Color.blue()
        )

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="remind")
    async def remind(self, ctx, time: str, *, reason: str = "No reason provided."):
        units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        duration = units.get(time[-1].lower())

        if not duration:
            return await ctx.reply(
                "Invalid time format. Use s, m, h, or d.",
                mention_author=False
            )

        try:
            seconds = int(time[:-1]) * duration
        except ValueError:
            return await ctx.reply(
                "Invalid duration.",
                mention_author=False
            )

        embed = discord.Embed(
            title="Reminder Set",
            description=(
                f"{ctx.author.mention}, I will remind you in **{time}** about:\n\n"
                f"{reason}"
            ),
            color=discord.Color.blue()
        )

        await ctx.reply(embed=embed, mention_author=False)

        await asyncio.sleep(seconds)

        reminder = discord.Embed(
            title="Reminder",
            description=(
                f"You asked to be reminded **{time}** ago about:\n\n"
                f"{reason}\n\n"
                f"[Jump to original message]({ctx.message.jump_url})"
            ),
            color=discord.Color.blue()
        )

        await ctx.author.send(embed=reminder)


async def setup(bot):
    bot.launch_time = datetime.datetime.utcnow()
    await bot.add_cog(Utility(bot))
