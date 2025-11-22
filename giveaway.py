import discord
from discord.ext import commands, tasks
import asyncio, random, json, os, time
from datetime import datetime

ACTIVE_FILE = "active_giveaways.json"
ENDED_FILE = "ended_giveaways.json"
GIVEAWAY_CONFIG = "giveaway_config.json"   # same file used by giveaway_config.py
CLAIMTIME_FILE = "claimtime_config.json"

# ---------------- JSON helpers ----------------
def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

active_giveaways = load_json(ACTIVE_FILE) or {}
ended_giveaways = load_json(ENDED_FILE) or {}
# giveaway_config is read from the same file path — keep name consistent
giveaway_config = load_json(GIVEAWAY_CONFIG) or {}
claimtime_config = load_json(CLAIMTIME_FILE) or {}

# ---------------- helpers ----------------
def convert_time(s: str) -> int:
    s = s.lower().strip()
    units = {"s":1,"m":60,"h":3600,"d":86400}
    if len(s) < 2:
        return 0
    unit = s[-1]
    if unit not in units:
        return 0
    try:
        v = int(s[:-1])
    except Exception:
        return 0
    return v * units[unit]

def build_blue_embed(title: str, desc: str = None):
    embed = discord.Embed(title=title, color=discord.Color.blurple())
    if desc:
        embed.description = desc
    return embed

def is_giveaway_manager():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        cfg = load_json(GIVEAWAY_CONFIG) or {}
        guild_cfg = cfg.get(str(ctx.guild.id), {})
        if isinstance(guild_cfg, int):
            guild_cfg = {}
        role_id = guild_cfg.get("manager_role")
        if role_id and discord.utils.get(ctx.author.roles, id=int(role_id)):
            return True
        raise commands.CheckFailure("❌ You don’t have permission to use giveaway commands.")
    return commands.check(predicate)

class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_giveaways.start()
        self.bot.loop.create_task(self.resume_active())

    def cog_unload(self):
        self.check_giveaways.cancel()

    # ---------------- start ----------------
    @commands.command(name="gstart")
    @is_giveaway_manager()
    async def gstart(self, ctx, duration: str, winners: int, *, prize: str):
        await ctx.message.delete()
        secs = convert_time(duration)
        if secs <= 0:
            return await ctx.send("❌ Invalid duration. Use s/m/h/d (e.g. 10s, 5m).")
        end_time = int(time.time()) + secs
        embed = discord.Embed(
            title=prize,
            description=(f"<:1000033547:1433343890831966208> **Hosted by:** {ctx.author.mention}\n"
                         f"<:1000033547:1433343890831966208> **Winners:** {winners}\n"
                         f"<:1000033547:1433343890831966208> **Ends:** <t:{end_time}:R>"),
            color=discord.Color.blurple()
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        msg = await ctx.send("🎉 **GIVEAWAY** 🎉", embed=embed)
        try:
            await msg.add_reaction("🎉")
        except Exception:
            pass

        active_giveaways[str(msg.id)] = {
            "guild_id": ctx.guild.id,
            "channel_id": ctx.channel.id,
            "message_id": msg.id,
            "host_id": ctx.author.id,
            "prize": prize,
            "winners": winners,
            "end_time": end_time,
            "created_at": int(time.time())
        }
        save_json(ACTIVE_FILE, active_giveaways)

        # send log embed to configured log channel (if any)
        await self.send_log_start(ctx.guild, prize, ctx.author, ctx.channel, end_time)

        # schedule end
        self.bot.loop.create_task(self.wait_and_end(msg.id))

    # ---------------- end ----------------
    @commands.command(name="gend")
    @is_giveaway_manager()
    async def gend(self, ctx):
        data = self.get_recent(ctx.channel.id, active_only=True)
        if not data:
            return await ctx.send("❌ No active giveaway found here.")
        await self.end_giveaway(str(data["message_id"]), manual=True)

    # ---------------- reroll ----------------
    @commands.command(name="greroll")
    @is_giveaway_manager()
    async def greroll(self, ctx):
        data = self.get_recent(ctx.channel.id)
        if not data:
            return await ctx.send("❌ No giveaway found here.")
        await self.reroll_giveaway(ctx, data)

    # ---------------- core tasks ----------------
    async def wait_and_end(self, msg_id):
        data = active_giveaways.get(str(msg_id))
        if not data:
            return
        remaining = data["end_time"] - int(time.time())
        if remaining > 0:
            await asyncio.sleep(remaining)
        if str(msg_id) in active_giveaways:
            await self.end_giveaway(str(msg_id))

    async def end_giveaway(self, key: str, manual=False):
        data = active_giveaways.get(key)
        if not data:
            return
        guild = self.bot.get_guild(data["guild_id"])
        if not guild:
            return
        channel = guild.get_channel(data["channel_id"])
        if not channel:
            return
        try:
            msg = await channel.fetch_message(int(key))
        except Exception:
            # message deleted — move to ended storage quietly
            data_copy = data.copy()
            data_copy["ended_at"] = int(time.time())
            ended_giveaways[key] = data_copy
            save_json(ENDED_FILE, ended_giveaways)
            active_giveaways.pop(key, None)
            save_json(ACTIVE_FILE, active_giveaways)
            return

        # load config fresh
        cfg = load_json(GIVEAWAY_CONFIG) or {}
        guild_cfg = cfg.get(str(guild.id), {}) or {}
        if isinstance(guild_cfg, int):
            guild_cfg = {}
        ban_role = guild_cfg.get("ban_role")

        participants = []
        for r in msg.reactions:
            if str(r.emoji) == "🎉":
                participants = [u async for u in r.users() if not u.bot]
                break

        if ban_role:
            participants = [u for u in participants if not discord.utils.get(u.roles, id=int(ban_role))]

        if not participants:
            await msg.reply("No valid participants found.")
            active_giveaways.pop(key, None)
            save_json(ACTIVE_FILE, active_giveaways)
            return

        winners = random.sample(participants, min(data.get("winners", 1), len(participants)))
        mentions = ", ".join(w.mention for w in winners)
        host = guild.get_member(data.get("host_id"))

        # edit giveaway message to ended embed
        ended_embed = discord.Embed(
            title="🎉 GIVEAWAY ENDED 🎉",
            description=(f"<:1000033547:1433343890831966208> **Winners:** {mentions}\n"
                         f"<:1000033547:1433343890831966208> **Hosted by:** {host.mention if host else 'Unknown'}"),
            color=discord.Color.blurple()
        )
        if guild.icon:
            ended_embed.set_thumbnail(url=guild.icon.url)

        try:
            await msg.edit(content="🎉 **GIVEAWAY ENDED 🎉**", embed=ended_embed)
        except Exception:
            pass

        # announcement in giveaway channel
        try:
            await msg.reply(f"🎉 Congratulations, {mentions}! You won **{data['prize']}**!")
        except Exception:
            pass

        # claimtime messages (in giveaway channel)
        for winner in winners:
            secs = self.get_claimtime_for_member(guild, winner)
            if secs and secs > 0:
                try:
                    await msg.reply(f"{secs} second claimtime")
                except Exception:
                    pass
                self.bot.loop.create_task(self.claimtime_notify(msg, secs))

        # move to ended store
        ended_giveaways[key] = {**data, "ended_at": int(time.time()), "last_winners": [u.id for u in winners]}
        active_giveaways.pop(key, None)
        save_json(ACTIVE_FILE, active_giveaways)
        save_json(ENDED_FILE, ended_giveaways)

        # log to configured channel
        await self.send_log_end(guild, data, mentions, host, channel)

    async def reroll_giveaway(self, ctx, data):
        guild = ctx.guild
        channel = guild.get_channel(data["channel_id"])
        try:
            msg = await channel.fetch_message(data["message_id"])
        except Exception:
            return await ctx.send("Could not fetch original giveaway message.")
        cfg = load_json(GIVEAWAY_CONFIG) or {}
        guild_cfg = cfg.get(str(guild.id), {}) or {}
        if isinstance(guild_cfg, int): guild_cfg = {}
        ban_role = guild_cfg.get("ban_role")

        participants = []
        for r in msg.reactions:
            if str(r.emoji) == "🎉":
                participants = [u async for u in r.users() if not u.bot]
                break

        if ban_role:
            participants = [u for u in participants if not discord.utils.get(u.roles, id=int(ban_role))]

        if not participants:
            return await ctx.send("❌ No participants to reroll.")

        winners = random.sample(participants, min(data.get("winners", 1), len(participants)))
        mentions = ", ".join(w.mention for w in winners)

        # reply announcing new winner(s)
        if len(winners) == 1:
            try:
                await msg.reply(f"🎉 The new winner is {mentions}! Congratulations!")
            except Exception:
                pass
        else:
            try:
                await msg.reply(f"🎉 The new winners are {mentions}! Congratulations!")
            except Exception:
                pass

        # claimtime for reroll winners (in giveaway channel)
        for winner in winners:
            secs = self.get_claimtime_for_member(guild, winner)
            if secs and secs > 0:
                try:
                    await msg.reply(f"{secs} second claimtime")
                except Exception:
                    pass
                self.bot.loop.create_task(self.claimtime_notify(msg, secs))

        # update ended storage (so greroll still remembers it)
        ended_giveaways[str(msg.id)] = {**data, "last_winners": [u.id for u in winners]}
        save_json(ENDED_FILE, ended_giveaways)

        # log reroll
        await self.send_log_reroll(guild, data, mentions, channel)

    async def claimtime_notify(self, msg, secs: int):
        await asyncio.sleep(secs)
        try:
            await msg.reply(f"{secs} seconds over!")
        except Exception:
            pass

    def get_claimtime_for_member(self, guild, member):
        cfg = load_json(CLAIMTIME_FILE) or {}
        rm = cfg.get(str(guild.id), {}).get("role_claimtimes", {}) or {}
        total = 0
        for r in member.roles:
            total += int(rm.get(str(r.id), 0) or 0)
        return total

    # ---------------- Logging helpers (embed style like your screenshot) ----------------
    async def send_log_start(self, guild, prize, host_member, giveaway_channel, end_time):
        cfg = load_json(GIVEAWAY_CONFIG) or {}
        guild_cfg = cfg.get(str(guild.id), {}) or {}
        log_channel_id = guild_cfg.get("log_channel")
        if not log_channel_id:
            return
        ch = guild.get_channel(int(log_channel_id))
        if not ch:
            return

        embed = discord.Embed(title="🎉 Giveaway Started", color=discord.Color.blurple())
        embed.add_field(name="Prize", value=prize, inline=False)
        embed.add_field(name="Host", value=host_member.mention, inline=True)
        embed.add_field(name="Channel", value=giveaway_channel.mention, inline=True)
        embed.add_field(name="Ends", value=f"<t:{end_time}:R>", inline=False)
        embed.timestamp = discord.utils.utcnow()
        try:
            await ch.send(embed=embed)
        except Exception:
            print(f"[giveaway] cannot send log to channel {log_channel_id}")

    async def send_log_end(self, guild, data, winners_mentions, host_member, giveaway_channel):
        cfg = load_json(GIVEAWAY_CONFIG) or {}
        guild_cfg = cfg.get(str(guild.id), {}) or {}
        log_channel_id = guild_cfg.get("log_channel")
        if not log_channel_id:
            return
        ch = guild.get_channel(int(log_channel_id))
        if not ch:
            return

        embed = discord.Embed(title="🏁 Giveaway Ended", color=discord.Color.blurple())
        embed.add_field(name="Prize", value=data.get("prize", "Unknown"), inline=False)
        embed.add_field(name="Host", value=host_member.mention if host_member else "Unknown", inline=True)
        embed.add_field(name="Winner(s)", value=winners_mentions or "None", inline=True)
        embed.add_field(name="Channel", value=giveaway_channel.mention, inline=False)
        embed.timestamp = discord.utils.utcnow()
        try:
            await ch.send(embed=embed)
        except Exception:
            print(f"[giveaway] cannot send log to channel {log_channel_id}")

    async def send_log_reroll(self, guild, data, winners_mentions, giveaway_channel):
        cfg = load_json(GIVEAWAY_CONFIG) or {}
        guild_cfg = cfg.get(str(guild.id), {}) or {}
        log_channel_id = guild_cfg.get("log_channel")
        if not log_channel_id:
            return
        ch = guild.get_channel(int(log_channel_id))
        if not ch:
            return

        embed = discord.Embed(title="🔁 Giveaway Rerolled", color=discord.Color.blurple())
        embed.add_field(name="Prize", value=data.get("prize", "Unknown"), inline=False)
        embed.add_field(name="New Winner(s)", value=winners_mentions or "None", inline=False)
        embed.add_field(name="Channel", value=giveaway_channel.mention, inline=False)
        embed.timestamp = discord.utils.utcnow()
        try:
            await ch.send(embed=embed)
        except Exception:
            print(f"[giveaway] cannot send log to channel {log_channel_id}")

    # ---------------- utilities ----------------
    def get_recent(self, channel_id, active_only=False):
        actives = [v for v in active_giveaways.values() if v["channel_id"] == channel_id]
        endeds = [v for v in ended_giveaways.values() if v["channel_id"] == channel_id]
        actives.sort(key=lambda x: x.get("end_time", 0), reverse=True)
        endeds.sort(key=lambda x: x.get("ended_at", x.get("created_at", 0)), reverse=True)
        if active_only:
            return actives[0] if actives else None
        return actives[0] if actives else (endeds[0] if endeds else None)

    @tasks.loop(seconds=60)
    async def check_giveaways(self):
        now = int(time.time())
        for key, data in list(active_giveaways.items()):
            if data.get("end_time", 0) <= now:
                await self.end_giveaway(key)

    async def resume_active(self):
        await asyncio.sleep(2)
        for key, data in list(active_giveaways.items()):
            remaining = data.get("end_time", 0) - int(time.time())
            if remaining <= 0:
                self.bot.loop.create_task(self.end_giveaway(key))
            else:
                self.bot.loop.create_task(self.wait_and_end(int(key)))

async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaway(bot))