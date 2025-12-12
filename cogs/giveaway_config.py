import discord
from discord.ext import commands
import json
import os

CONFIG_PATH = "giveaway_config.json"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[giveaway_config] load error: {e}")
        return {}


def save_config(data):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[giveaway_config] save error: {e}")


giveaway_config = load_config()


def build_blue_embed(title: str, desc: str):
    return discord.Embed(title=title, description=desc, color=discord.Color.blurple())


class GiveawayConfig(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("[giveaway_config] Cog loaded")

    @commands.command(name="giveaway_log")
    @commands.has_permissions(administrator=True)
    async def giveaway_log(self, ctx: commands.Context, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        giveaway_config.setdefault(guild_id, {})["log_channel"] = channel.id
        save_config(giveaway_config)

        try:
            await ctx.send(embed=build_blue_embed("Log Channel Set", f"Giveaway logs will be sent to {channel.mention}."))
        except discord.Forbidden:
            await ctx.send(f"Giveaway log channel set to {channel.mention}.")

    @commands.command(name="giveaway_ban")
    @commands.has_permissions(administrator=True)
    async def giveaway_ban(self, ctx: commands.Context, role: discord.Role):
        guild_id = str(ctx.guild.id)
        giveaway_config.setdefault(guild_id, {})["ban_role"] = role.id
        save_config(giveaway_config)

        try:
            await ctx.send(embed=build_blue_embed("Ban Role Set", f"Members with {role.mention} cannot join giveaways."))
        except discord.Forbidden:
            await ctx.send(f"Ban role set to {role.mention}.")

    @commands.command(name="setmanager")
    @commands.has_permissions(administrator=True)
    async def setmanager(self, ctx: commands.Context, role: discord.Role):
        guild_id = str(ctx.guild.id)
        giveaway_config.setdefault(guild_id, {})["manager_role"] = role.id
        save_config(giveaway_config)

        try:
            await ctx.send(embed=build_blue_embed("Manager Role Set", f"{role.mention} can now manage giveaways."))
        except discord.Forbidden:
            await ctx.send(f"Manager role set to {role.mention}.")

    @commands.command(name="giveaway_config")
    @commands.has_permissions(administrator=True)
    async def giveaway_config_cmd(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        cfg = giveaway_config.get(guild_id, {})
        manager = cfg.get("manager_role")
        log = cfg.get("log_channel")
        ban = cfg.get("ban_role")

        embed = discord.Embed(title="Giveaway Configuration", color=discord.Color.blurple())
        embed.add_field(name="Log Channel", value=f"<#{log}>" if log else "Not set", inline=False)
        embed.add_field(name="Manager Role", value=f"<@&{manager}>" if manager else "Not set", inline=False)
        embed.add_field(name="Banned Role", value=f"<@&{ban}>" if ban else "Not set", inline=False)

        try:
            await ctx.send(embed=embed)
        except discord.Forbidden:
            body = (
                f"Log Channel: {('<#'+str(log)+'>') if log else 'Not set'}\n"
                f"Manager Role: {('<@&'+str(manager)+'>') if manager else 'Not set'}\n"
                f"Banned Role: {('<@&'+str(ban)+'>') if ban else 'Not set'}"
            )
            await ctx.send(body)


async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawayConfig(bot))
