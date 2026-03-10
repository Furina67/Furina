import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import aiosqlite
import asyncio

DB_PATH = "/home/container/afk.db"

ACTIVATE_IMAGE = "https://ik.imagekit.io/mzxm6xoasi/furina.jpg"
PING_IMAGE = "https://ik.imagekit.io/jxgzuguk6/image0.png"
REMOVAL_IMAGE = "https://ik.imagekit.io/mzxm6xoasi/genshin-impact-focalors-demo.jpg"


class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = None
        self.write_lock = asyncio.Lock()

    async def cog_load(self):
        self.db = await aiosqlite.connect(DB_PATH)
        await self.db.execute("PRAGMA journal_mode=WAL;")
        await self.db.execute("PRAGMA busy_timeout = 5000;")
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS afk (
                user_id INTEGER PRIMARY KEY,
                reason TEXT,
                since TEXT
            )
        """)
        await self.db.commit()

    async def cog_unload(self):
        if self.db:
            await self.db.close()

    async def db_read(self, query, params=()):
        async with self.db.execute(query, params) as cursor:
            return await cursor.fetchone()

    async def db_write(self, query, params=()):
        async with self.write_lock:
            await self.db.execute(query, params)
            await self.db.commit()

    def format_duration(self, delta):
        secs = int(delta.total_seconds())
        mins, secs = divmod(secs, 60)
        hrs, mins = divmod(mins, 60)
        return f"{hrs}h {mins}m {secs}s"

    def format_ago(self, delta):
        secs = int(delta.total_seconds())
        mins, secs = divmod(secs, 60)
        hrs, mins = divmod(mins, 60)
        return f"{hrs}h {mins}m {secs}s ago"

    @commands.hybrid_command(name="afk", description="Set your AFK status")
    @app_commands.describe(reason="Reason for being AFK")
    async def afk(self, ctx, *, reason: str = "AFK"):

        existing = await self.db_read(
            "SELECT reason, since FROM afk WHERE user_id = ?",
            (ctx.author.id,)
        )

        # If already AFK
        if existing:
            since = datetime.fromisoformat(existing[1])
            duration = self.format_duration(
                datetime.now(timezone.utc) - since
            )

            view = discord.ui.LayoutView()
            container = discord.ui.Container()

            container.add_item(
                discord.ui.TextDisplay(
                    f"**You're already AFK!**\n"
                    f"Reason: {existing[0]}\n"
                    f"Since: {duration}"
                )
            )

            container.add_item(discord.ui.Separator())

            gallery = discord.ui.MediaGallery()
            gallery.add_item(media=PING_IMAGE)
            container.add_item(gallery)

            view.add_item(container)

            if ctx.interaction:
                await ctx.interaction.response.send_message(
                    view=view,
                    ephemeral=True,
                    allowed_mentions=discord.AllowedMentions.none()
                )
            else:
                await ctx.reply(
                    view=view,
                    allowed_mentions=discord.AllowedMentions.none()
                )
            return

        # Not AFK yet â†’ set AFK
        await self.db_write(
            "INSERT INTO afk (user_id, reason, since) VALUES (?, ?, ?)",
            (ctx.author.id, reason, datetime.now(timezone.utc).isoformat())
        )

        view = discord.ui.LayoutView()
        container = discord.ui.Container()

        container.add_item(
            discord.ui.TextDisplay(
                f"**AFK Activated**\n"
                f"You are now AFK globally.\n"
                f"Reason: {reason}"
            )
        )

        container.add_item(discord.ui.Separator())

        gallery = discord.ui.MediaGallery()
        gallery.add_item(media=ACTIVATE_IMAGE)
        container.add_item(gallery)

        view.add_item(container)

        if ctx.interaction:
            await ctx.interaction.response.send_message(
                view=view,
                allowed_mentions=discord.AllowedMentions.none()
            )
        else:
            await ctx.reply(
                view=view,
                allowed_mentions=discord.AllowedMentions.none()
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        # If author was AFK
        row = await self.db_read(
            "SELECT reason, since FROM afk WHERE user_id = ?",
            (message.author.id,)
        )

        if row:
            await self.db_write(
                "DELETE FROM afk WHERE user_id = ?",
                (message.author.id,)
            )

            since = datetime.fromisoformat(row[1])
            duration = self.format_duration(
                datetime.now(timezone.utc) - since
            )

            view = discord.ui.LayoutView()
            container = discord.ui.Container()

            container.add_item(
                discord.ui.TextDisplay(
                    f"**Welcome back {message.author.display_name}!**\n"
                    f"You were AFK for **{duration}**."
                )
            )

            container.add_item(discord.ui.Separator())

            gallery = discord.ui.MediaGallery()
            gallery.add_item(media=REMOVAL_IMAGE)
            container.add_item(gallery)

            view.add_item(container)

            await message.reply(
                view=view,
                allowed_mentions=discord.AllowedMentions.none()
            )
            return

        # Check mentions
        for mention in message.mentions:
            row = await self.db_read(
                "SELECT reason, since FROM afk WHERE user_id = ?",
                (mention.id,)
            )

            if row:
                ago = self.format_ago(
                    datetime.now(timezone.utc) - datetime.fromisoformat(row[1])
                )

                view = discord.ui.LayoutView()
                container = discord.ui.Container()

                container.add_item(
                    discord.ui.TextDisplay(
                        f"**{mention.display_name} is AFK**\n"
                        f"Reason: {row[0]}\n"
                        f"Since: {ago}"
                    )
                )

                container.add_item(discord.ui.Separator())

                gallery = discord.ui.MediaGallery()
                gallery.add_item(media=PING_IMAGE)
                container.add_item(gallery)

                view.add_item(container)

                await message.channel.send(
                    view=view,
                    allowed_mentions=discord.AllowedMentions.none()
                )
                break


async def setup(bot):
    await bot.add_cog(AFK(bot))