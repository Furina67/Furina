import discord
from discord.ext import commands
from datetime import timedelta
from typing import Optional
import re

TICK = "✅"

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.time_regex = re.compile(r"(\d+)([smhd])$")

    def parse_time(self, time_str: str) -> Optional[timedelta]:
        match = self.time_regex.match(time_str)
        if not match:
            return None
        value, unit = int(match.group(1)), match.group(2)
        if unit == "s":
            return timedelta(seconds=value)
        if unit == "m":
            return timedelta(minutes=value)
        if unit == "h":
            return timedelta(hours=value)
        if unit == "d":
            return timedelta(days=value)

    async def can_moderate(self, ctx, member: discord.Member):
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

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        can_mod, msg = await self.can_moderate(ctx, member)
        if not can_mod:
            return await ctx.reply(msg, mention_author=False)

        await member.kick(reason=f"{reason} | By {ctx.author}")
        embed = discord.Embed(
            description=f"{TICK} **{member.mention}** was kicked.\n📝 **Reason:** {reason}",
            color=discord.Color.orange()
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        can_mod, msg = await self.can_moderate(ctx, member)
        if not can_mod:
            return await ctx.reply(msg, mention_author=False)

        await member.ban(reason=f"{reason} | By {ctx.author}")
        embed = discord.Embed(
            description=f"{TICK} **{member.mention}** was banned.\n📝 **Reason:** {reason}",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, user: str):
        bans = [entry async for entry in ctx.guild.bans(limit=1000)]
        for entry in bans:
            if user in (str(entry.user), entry.user.name, str(entry.user.id)):
                await ctx.guild.unban(entry.user, reason=f"Unbanned by {ctx.author}")
                embed = discord.Embed(
                    description=f"{TICK} **{entry.user}** has been unbanned.",
                    color=discord.Color.green()
                )
                return await ctx.reply(embed=embed, mention_author=False)

        await ctx.reply("❌ User not found in ban list.", mention_author=False)

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

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def setnick(self, ctx, member: discord.Member, *, nickname: str):
        await member.edit(nick=nickname)
        embed = discord.Embed(
            description=f"{TICK} Successfully changed **{member.mention}**’s nickname to **{nickname}**.",
            color=discord.Color.blue()
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def resetnick(self, ctx, member: discord.Member):
        await member.edit(nick=None)
        embed = discord.Embed(
            description=f"{TICK} Successfully reset **{member.mention}**’s nickname.",
            color=discord.Color.green()
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, member: discord.Member, *, role_input: str):
        role = None
        mention = re.match(r"<@&(\d+)>", role_input)
        if mention:
            role = discord.utils.get(ctx.guild.roles, id=int(mention.group(1)))
        elif role_input.isdigit():
            role = discord.utils.get(ctx.guild.roles, id=int(role_input))
        else:
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
