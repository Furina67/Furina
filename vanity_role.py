# cogs/vanity_role.py
# ===================
# Single Vanity Role System (Embed version)
# Users get a specific role when their status contains a chosen word.

import discord
from discord.ext import commands
import json
import os

DATA_FILE = "vanity_data.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


class VanityRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    # -------------------------------------------
    # Commands
    # -------------------------------------------
    @commands.command(name="setvanity")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def set_vanity(self, ctx, word: str, role: discord.Role):
        """Set the server's vanity word and role."""
        self.data[str(ctx.guild.id)] = {
            "word": word,
            "role_id": role.id
        }
        save_data(self.data)

        embed = discord.Embed(
            title="<a:1000033630:1433575320782372995> Vanity Role Set!",
            description=f"**Word:** `{word}`\n**Role:** {role.mention}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Configured by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="removevanity")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def remove_vanity(self, ctx):
        """Remove the server's vanity setup."""
        if str(ctx.guild.id) not in self.data:
            embed = discord.Embed(
                title="❌ No Vanity Setup Found",
                description="There is no vanity word set for this server.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        del self.data[str(ctx.guild.id)]
        save_data(self.data)

        embed = discord.Embed(
            title="Vanity Role Removed",
            description="The vanity system has been disabled for this server.",
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Action by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="vanityinfo")
    @commands.guild_only()
    async def vanity_info(self, ctx):
        """Show the current vanity setup."""
        setup = self.data.get(str(ctx.guild.id))
        if not setup:
            embed = discord.Embed(
                title="Vanity System Info",
                description="No vanity word is currently set for this server.",
                color=discord.Color.blurple()
            )
            return await ctx.send(embed=embed)

        role = ctx.guild.get_role(setup["role_id"])
        embed = discord.Embed(
            title="Current Vanity Role Setup",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Word", value=f"`{setup['word']}`", inline=False)
        embed.add_field(name="Role", value=role.mention if role else "(deleted role)", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    # -------------------------------------------
    # Presence Listener
    # -------------------------------------------
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if not after.guild:
            return

        guild_id = str(after.guild.id)
        if guild_id not in self.data:
            return

        setup = self.data[guild_id]
        word = setup["word"]
        role = after.guild.get_role(setup["role_id"])
        if not role:
            return

        # Get user's custom status
        custom_status = None
        for activity in after.activities:
            if isinstance(activity, discord.CustomActivity) and activity.name:
                custom_status = activity.name
                break

        try:
            if custom_status and word.lower() in custom_status.lower():
                if role not in after.roles:
                    await after.add_roles(role, reason="Vanity keyword in status")
            else:
                if role in after.roles:
                    await after.remove_roles(role, reason="Vanity keyword removed")
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"[VanityRole Error] {e}")


async def setup(bot):
    await bot.add_cog(VanityRole(bot))