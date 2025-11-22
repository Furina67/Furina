import discord
from discord.ext import commands
from datetime import timedelta
from typing import Optional
import re

TICK = "<a:1000033630:1433575320782372995>"

# =========================
# MODERATION CLASS
# =========================
class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Helper to parse time like 10s, 5m, 2h, 1d
    def parse_time(self, time_str: str) -> Optional[timedelta]:
        match = re.match(r"(\d+)([smhd])$", time_str)
        if not match:
            return None
        value, unit = int(match[1]), match[2]
        if unit == "s":
            return timedelta(seconds=value)
        elif unit == "m":
            return timedelta(minutes=value)
        elif unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)

    async def can_moderate(self, ctx, member: discord.Member) -> tuple[bool, str]:
        if member == ctx.author:
            return False, "❌ You cannot moderate yourself."
        if member == ctx.guild.me:
            return False, "❌ I cannot moderate myself."
        if member.id == ctx.guild.owner_id:
            return False, "❌ You cannot moderate the server owner."
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return False, "❌ You cannot moderate someone with an equal or higher role."
        if member.top_role >= ctx.guild.me.top_role:
            return False, "❌ I cannot moderate someone with an equal or higher role than mine."
        return True, ""

    # Timeout command
    @commands.command(aliases=["to"])
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, time: str, *, reason="No reason provided"):
        duration = self.parse_time(time)
        if not duration:
            return await ctx.reply("❌ Invalid duration. Use formats like `10s`, `5m`, `2h`, or `1d`.", mention_author=False)

        can_mod, msg = await self.can_moderate(ctx, member)
        if not can_mod:
            return await ctx.reply(msg, mention_author=False)

        try:
            await member.edit(timed_out_until=discord.utils.utcnow() + duration, reason=f"{reason} | By {ctx.author}")
            embed = discord.Embed(
                description=f"{TICK} **{member.mention}** has been timed out for **{time}**.\n📝 **Reason:** {reason}",
                color=discord.Color.blue()
            )
            await ctx.reply(embed=embed, mention_author=False)
        except Exception as e:
            await ctx.reply(f"❌ Error: {e}", mention_author=False)

    @commands.command(aliases=["rto"])
    @commands.has_permissions(moderate_members=True)
    async def removetimeout(self, ctx, member: discord.Member):
        try:
            await member.edit(timed_out_until=None, reason=f"Timeout removed by {ctx.author}")
            embed = discord.Embed(
                description=f"{TICK} Timeout removed for **{member.mention}**.",
                color=discord.Color.green()
            )
            await ctx.reply(embed=embed, mention_author=False)
        except Exception as e:
            await ctx.reply(f"❌ Error: {e}", mention_author=False)

    # Kick
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        can_mod, msg = await self.can_moderate(ctx, member)
        if not can_mod:
            return await ctx.reply(msg, mention_author=False)
        await member.kick(reason=f"{reason} | By {ctx.author}")
        await ctx.reply(embed=discord.Embed(description=f"{TICK} **{member.mention}** was kicked.\n📝 **Reason:** {reason}", color=discord.Color.orange()), mention_author=False)

    # Ban
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        can_mod, msg = await self.can_moderate(ctx, member)
        if not can_mod:
            return await ctx.reply(msg, mention_author=False)
        await member.ban(reason=f"{reason} | By {ctx.author}")
        await ctx.reply(embed=discord.Embed(description=f"{TICK} **{member.mention}** was banned.\n📝 **Reason:** {reason}", color=discord.Color.red()), mention_author=False)

    # Unban
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, user: str):
        bans = [entry async for entry in ctx.guild.bans(limit=1000)]
        for entry in bans:
            if user in (str(entry.user), entry.user.name, str(entry.user.id)):
                await ctx.guild.unban(entry.user, reason=f"Unbanned by {ctx.author}")
                return await ctx.reply(embed=discord.Embed(description=f"{TICK} **{entry.user}** has been unbanned.", color=discord.Color.green()), mention_author=False)
        await ctx.reply("❌ User not found in ban list.", mention_author=False)

    # Lock / Unlock
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.reply(embed=discord.Embed(description=f"{TICK} Channel locked.", color=discord.Color.blue()), mention_author=False)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.reply(embed=discord.Embed(description=f"{TICK} Channel unlocked.", color=discord.Color.green()), mention_author=False)

    # Hide / Unhide
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def hide(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.reply(embed=discord.Embed(description=f"{TICK} Channel hidden.", color=discord.Color.blue()), mention_author=False)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unhide(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = True
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.reply(embed=discord.Embed(description=f"{TICK} Channel unhidden.", color=discord.Color.green()), mention_author=False)

    # Nickname
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def setnick(self, ctx, member: discord.Member, *, nickname: str):
        await member.edit(nick=nickname)
        await ctx.reply(embed=discord.Embed(description=f"{TICK} Successfully changed **{member.mention}**’s nickname to **{nickname}**.", color=discord.Color.blue()), mention_author=False)

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def resetnick(self, ctx, member: discord.Member):
        await member.edit(nick=None)
        await ctx.reply(embed=discord.Embed(description=f"{TICK} Successfully reset **{member.mention}**’s nickname.", color=discord.Color.green()), mention_author=False)

    # Role toggle (supports mention, ID, or name)
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, member: discord.Member, *, role_input: str):
        role = None

        # Check if it's a mention: <@&role_id>
        mention_match = re.match(r"<@&(\d+)>", role_input)
        if mention_match:
            role_id = int(mention_match.group(1))
            role = discord.utils.get(ctx.guild.roles, id=role_id)
        # Check if input is a numeric ID
        elif role_input.isdigit():
            role = discord.utils.get(ctx.guild.roles, id=int(role_input))
        # Fallback: search by name (case-insensitive)
        if not role:
            role = discord.utils.find(lambda r: r.name.lower() == role_input.lower(), ctx.guild.roles)

        if not role:
            return await ctx.reply("❌ Role not found.", mention_author=False)

        if role >= ctx.guild.me.top_role:
            return await ctx.reply("❌ That role is higher than or equal to my top role.", mention_author=False)
        if role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply("❌ That role is higher than or equal to your top role.", mention_author=False)

        if role in member.roles:
            await member.remove_roles(role)
            desc = f"{TICK} Removed **{role.name}** from **{member.mention}**."
            color = discord.Color.red()
        else:
            await member.add_roles(role)
            desc = f"{TICK} Gave **{role.name}** to **{member.mention}**."
            color = discord.Color.green()

        await ctx.reply(embed=discord.Embed(description=desc, color=color), mention_author=False)

async def setup(bot):
    await bot.add_cog(Moderation(bot))