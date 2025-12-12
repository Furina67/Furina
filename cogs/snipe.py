import discord
from discord.ext import commands
from collections import deque
import json
from datetime import datetime, timezone

SNIPE_FILE = "snipe.json"
SETTINGS_FILE = "snipe_settings.json"


def utcnow_iso():
    return datetime.now(timezone.utc).isoformat()


def parse_time(value: str):
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)


class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # load deleted messages
        try:
            with open(SNIPE_FILE, "r") as f:
                data = json.load(f)
                self.snipes = {int(k): deque(v, maxlen=10) for k, v in data.items()}
        except Exception:
            self.snipes = {}

        # load snipe role settings
        try:
            with open(SETTINGS_FILE, "r") as f:
                self.settings = json.load(f)
        except Exception:
            self.settings = {}

    def save_snipes(self):
        with open(SNIPE_FILE, "w") as f:
            json.dump({str(k): list(v) for k, v in self.snipes.items()}, f, indent=4)

    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)

    # -------------------------
    # LISTENER — save deleted msg
    # -------------------------
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        saved = self.snipes.setdefault(message.channel.id, deque(maxlen=10))

        saved.appendleft({
            "author_id": message.author.id,
            "author_name": message.author.name,
            "content": message.content,
            "attachments": [a.url for a in message.attachments],
            "time": utcnow_iso()
        })

        self.save_snipes()

    # -------------------------
    # PERMISSION CHECK
    # -------------------------
    def has_snipe_permission(self, ctx):
        role_id = self.settings.get(str(ctx.guild.id))
        if not role_id:
            return True
        role = ctx.guild.get_role(role_id)
        return role in ctx.author.roles if role else False

    # -------------------------
    # SNIPE COMMAND
    # -------------------------
    @commands.command(name="snipe")
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def snipe(self, ctx, arg: str = None):
        if not self.has_snipe_permission(ctx):
            return await ctx.send("You do not have permission to use this command.")

        messages = self.snipes.get(ctx.channel.id)
        if not messages:
            return await ctx.send("There is nothing to snipe.")

        # -------------------------
        # SNIPE ALL
        # -------------------------
        if arg and arg.lower() == "all":
            embed = discord.Embed(
                title=f"Deleted Messages in #{ctx.channel.name}",
                color=discord.Color.blue()
            )

            for idx, msg in enumerate(messages, start=1):
                utc_time = parse_time(msg["time"])
                timestamp = int(utc_time.timestamp())
                content = msg["content"] or "[Attachment Only]"

                value = (
                    f"Author: <@{msg['author_id']}>\n"
                    f"Content: {content}\n"
                )

                if msg["attachments"]:
                    for i, att in enumerate(msg["attachments"], start=1):
                        value += f"Attachment {i}: {att}\n"

                embed.add_field(
                    name=f"{idx}. Deleted at <t:{timestamp}:f>",
                    value=value,
                    inline=False
                )

            return await ctx.send(embed=embed)

        # -------------------------
        # SINGLE SNIPE
        # -------------------------
        await self.send_single_snipe(ctx, messages[0])

    # -------------------------
    # SINGLE SNIPE EMBED
    # -------------------------
    async def send_single_snipe(self, ctx, msg):
        member = ctx.guild.get_member(msg["author_id"])

        embed = discord.Embed(
            description=msg["content"] or "[Attachment Only]",
            color=discord.Color.blue()
        )

        if member:
            embed.set_author(
                name=member.display_name,
                icon_url=member.display_avatar.url
            )
        else:
            embed.set_author(name=msg["author_name"])

        embed.timestamp = parse_time(msg["time"])

        if msg["attachments"]:
            for i, att in enumerate(msg["attachments"], start=1):
                embed.add_field(
                    name=f"Attachment {i}",
                    value=att,
                    inline=False
                )

        await ctx.send(embed=embed)

    # -------------------------
    # SETTINGS
    # -------------------------
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def snipesettings(self, ctx, *, role_input: str = None):

        if role_input is None:
            rid = self.settings.get(str(ctx.guild.id))
            if rid:
                role = ctx.guild.get_role(rid)
                name = role.name if role else "Unknown"
                return await ctx.send(
                    f"Current snipe role: {name}\n"
                    "Use `.snipesettings <role>` to change it."
                )
            return await ctx.send("No snipe role set. Everyone can use snipe.")

        if role_input.lower() in ("clear", "reset"):
            self.settings.pop(str(ctx.guild.id), None)
            self.save_settings()
            return await ctx.send("Snipe role restriction removed.")

        role = None
        if ctx.message.role_mentions:
            role = ctx.message.role_mentions[0]
        elif role_input.isdigit():
            role = ctx.guild.get_role(int(role_input))
        else:
            role = discord.utils.find(
                lambda r: r.name.lower() == role_input.lower(),
                ctx.guild.roles
            )

        if not role:
            return await ctx.send(f"Role not found: {role_input}")

        self.settings[str(ctx.guild.id)] = role.id
        self.save_settings()
        await ctx.send(f"Snipe role set to {role.name}")

    # -------------------------
    # COOLDOWN ERROR
    # -------------------------
    @snipe.error
    async def snipe_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"Try again in {error.retry_after:.1f} seconds.",
                delete_after=3
            )


async def setup(bot):
    await bot.add_cog(Snipe(bot))
