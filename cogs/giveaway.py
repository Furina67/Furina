import discord
from discord.ext import commands, tasks
import sqlite3
import random
from datetime import datetime, timedelta
import re

DB_PATH = "giveaways.db"

ENTRY_EMOJI = "<a:Furina_play:1475973589617606847>"
GIVEAWAY_EMOJI = "<:giveaway:1476099137844936877>"
DOT = "<:BlueDot:1477069909296025762>"


def parse_duration(value: str) -> int:
    value = value.lower().strip()
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if len(value) < 2:
        return 0
    unit = value[-1]
    if unit not in units:
        return 0
    try:
        amount = int(value[:-1])
    except:
        return 0
    return amount * units[unit]


class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.init_db()
        self.bot.loop.create_task(self.resume_giveaways())
        self.check_giveaways.start()

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use giveaway commands.")

    def init_db(self):
        with sqlite3.connect(DB_PATH) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS giveaways (
                    message_id INTEGER PRIMARY KEY,
                    giveaway_id TEXT,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    host_id INTEGER,
                    prize TEXT,
                    winners INTEGER,
                    end_timestamp INTEGER,
                    ended INTEGER DEFAULT 0
                )
            """)
            db.commit()

    def db(self, query, params=(), fetchone=False):
        with sqlite3.connect(DB_PATH) as db:
            cur = db.execute(query, params)
            db.commit()
            return cur.fetchone() if fetchone else cur.fetchall()

    @commands.command(name="gstart")
    @commands.has_permissions(manage_guild=True)
    async def gstart(self, ctx, duration: str, winners: int, *, prize: str):

        if winners < 1 or winners > 100:
            return await ctx.send(
                "Maximum winners count is 100. Please use a number between 1 and 100."
            )

        existing = self.db(
            "SELECT 1 FROM giveaways WHERE channel_id=? AND ended=0",
            (ctx.channel.id,),
            fetchone=True
        )

        if existing:
            return await ctx.send("There is already an active giveaway in this channel.")

        seconds = parse_duration(duration)
        if seconds <= 0:
            return await ctx.send("Invalid duration. Use 10s, 5m, 1h, 1d.")

        now = datetime.now()
        end_dt = now + timedelta(seconds=seconds)
        end_timestamp = int(end_dt.timestamp())

        embed = discord.Embed(
            title=f"{GIVEAWAY_EMOJI} {prize} {GIVEAWAY_EMOJI}",
            color=discord.Color.from_rgb(0, 200, 255)
        )

        embed.description = (
            f"{DOT} **Winners:** {winners}\n"
            f"{DOT} **Entries:** 0\n"
            f"{DOT} **Ends:** <t:{end_timestamp}:R>\n"
            f"{DOT} **Hosted by:** {ctx.author.mention}\n\n"
            f"React with {ENTRY_EMOJI} to participate!"
        )

        msg = await ctx.send(embed=embed)
        await msg.add_reaction(ENTRY_EMOJI)

        giveaway_id = str(msg.id)[-4:]
        embed.set_footer(text=f"ID: {giveaway_id}")
        await msg.edit(embed=embed)

        self.db(
            "INSERT INTO giveaways VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)",
            (
                msg.id,
                giveaway_id,
                ctx.guild.id,
                ctx.channel.id,
                ctx.author.id,
                prize,
                winners,
                end_timestamp
            )
        )

    @commands.command(name="gend")
    @commands.has_permissions(manage_guild=True)
    async def gend(self, ctx, giveaway_id: str):
        row = self.db(
            "SELECT * FROM giveaways WHERE giveaway_id=? AND ended=0",
            (giveaway_id,),
            fetchone=True
        )

        if not row:
            return await ctx.send("No active giveaway found with that ID.")

        await self.end_giveaway(row[0])

    @commands.command(name="greroll")
    @commands.has_permissions(manage_guild=True)
    async def greroll(self, ctx, giveaway_id: str):
        row = self.db(
            "SELECT * FROM giveaways WHERE giveaway_id=? AND ended=1",
            (giveaway_id,),
            fetchone=True
        )

        if not row:
            return await ctx.send("No ended giveaway found with that ID.")

        await self.pick_winner(row, reroll=True)

    async def resume_giveaways(self):
        await self.bot.wait_until_ready()
        now = int(datetime.now().timestamp())

        rows = self.db(
            "SELECT message_id FROM giveaways WHERE ended=0 AND end_timestamp<=?",
            (now,)
        )

        for (message_id,) in rows:
            await self.end_giveaway(message_id)

    async def end_giveaway(self, message_id):

        row = self.db(
            "SELECT ended FROM giveaways WHERE message_id=?",
            (message_id,),
            fetchone=True
        )

        if not row or row[0] == 1:
            return

        self.db(
            "UPDATE giveaways SET ended=1 WHERE message_id=?",
            (message_id,)
        )

        full_row = self.db(
            "SELECT * FROM giveaways WHERE message_id=?",
            (message_id,),
            fetchone=True
        )

        await self.pick_winner(full_row)

    async def pick_winner(self, row, reroll=False):
        message_id, giveaway_id, guild_id, channel_id, host_id, prize, winner_count, end_ts, ended = row

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(message_id)
        except:
            return

        participants = []
        for reaction in message.reactions:
            if str(reaction.emoji) == ENTRY_EMOJI:
                participants = [u async for u in reaction.users() if not u.bot]
                break

        if not participants:
            await channel.send("No valid participants.")
            return

        winners = random.sample(participants, min(winner_count, len(participants)))
        winner_mentions = ", ".join(w.mention for w in winners)

        if reroll:
            await channel.send(
                f"{GIVEAWAY_EMOJI} The new winner(s): {winner_mentions}"
            )
            return

        valid_count = len(participants)

        embed = discord.Embed(
            title=f"{GIVEAWAY_EMOJI} {prize} {GIVEAWAY_EMOJI}",
            color=discord.Color.from_rgb(0, 90, 255)
        )

        embed.description = (
            f"{DOT} **Hosted by:** <@{host_id}>\n"
            f"{DOT} **Valid Entries:** {valid_count}\n\n"
            f"{DOT} **Winners:** {winner_mentions}\n\n"
            f"ðŸ”’ Entries Closed"
        )

        embed.set_footer(text=f"ID: {giveaway_id}")

        await message.edit(embed=embed)

        await channel.send(
            f"{GIVEAWAY_EMOJI} Congratulations {winner_mentions}! You won **{prize}** {GIVEAWAY_EMOJI}"
        )

    @tasks.loop(seconds=10)
    async def check_giveaways(self):
        now = int(datetime.now().timestamp())

        rows = self.db(
            "SELECT * FROM giveaways WHERE ended=0",
        )

        for row in rows:
            message_id, giveaway_id, guild_id, channel_id, host_id, prize, winner_count, end_ts, ended = row

            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue

            channel = guild.get_channel(channel_id)
            if not channel:
                continue

            try:
                message = await channel.fetch_message(message_id)
            except:
                continue

            if end_ts <= now:
                await self.end_giveaway(message_id)
                continue

            participants = []
            for reaction in message.reactions:
                if str(reaction.emoji) == ENTRY_EMOJI:
                    participants = [u async for u in reaction.users() if not u.bot]
                    break

            entry_count = len(participants)

            embed = message.embeds[0]
            desc = embed.description

            new_desc = re.sub(
                r"\*\*Entries:\*\* \d+",
                f"**Entries:** {entry_count}",
                desc
            )

            if new_desc != desc:
                embed.description = new_desc
                await message.edit(embed=embed)

    @check_giveaways.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaway(bot))