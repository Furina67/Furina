import discord
from discord.ext import commands
from datetime import datetime, timezone
import json
import os

AFK_FILE = "afk_data.json"


class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = self.load_afk_data()

    def load_afk_data(self):
        if not os.path.exists(AFK_FILE):
            return {}

        with open(AFK_FILE, "r") as f:
            data = json.load(f)

        for uid, info in data.items():
            info["since"] = datetime.fromisoformat(info["since"])

        return data

    def save_afk_data(self):
        formatted = {
            str(uid): {
                "reason": d["reason"],
                "since": d["since"].isoformat()
            }
            for uid, d in self.afk_users.items()
        }
        with open(AFK_FILE, "w") as f:
            json.dump(formatted, f, indent=4)

    def format_duration(self, delta):
        secs = int(delta.total_seconds())
        if secs < 60:
            return f"{secs} seconds"
        mins, secs = divmod(secs, 60)
        if mins < 60:
            return f"{mins} minutes {secs} seconds"
        hrs, mins = divmod(mins, 60)
        return f"{hrs}h {mins}m {secs}s"

    def format_ago(self, delta):
        secs = int(delta.total_seconds())
        if secs < 60:
            return f"{secs} seconds ago"
        mins, secs = divmod(secs, 60)
        if mins < 60:
            return f"{mins} minutes ago"
        hrs, mins = divmod(mins, 60)
        return f"{hrs} hours ago"

    @commands.command(name="afk")
    async def afk(self, ctx, *, reason: str = "AFK"):
        self.afk_users[ctx.author.id] = {
            "reason": reason,
            "since": datetime.now(timezone.utc)
        }
        self.save_afk_data()

        embed = discord.Embed(
            title="AFK Activated",
            description=f"You are now marked as AFK.\nReason: {reason}",
            color=discord.Color.blurple()
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        if message.author.id in self.afk_users:
            info = self.afk_users.pop(message.author.id)
            self.save_afk_data()

            delta = datetime.now(timezone.utc) - info["since"]
            duration = self.format_duration(delta)

            embed = discord.Embed(
                title="AFK Removed",
                description=f"Welcome back {message.author.display_name}!\nYou were AFK for {duration}.",
                color=discord.Color.blue()
            )
            await message.reply(embed=embed, mention_author=False)
            return

        for mention in message.mentions:
            if mention.id in self.afk_users:
                info = self.afk_users[mention.id]
                delta = datetime.now(timezone.utc) - info["since"]

                embed = discord.Embed(
                    description=f"{mention.display_name} is AFK — {info['reason']} ({self.format_ago(delta)}).",
                    color=discord.Color.blue()
                )
                await message.channel.send(embed=embed)
                break


async def setup(bot):
    await bot.add_cog(AFK(bot))
