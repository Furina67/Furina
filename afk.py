import discord
from discord.ext import commands
from datetime import datetime, timezone
import json, os

AFK_FILE = "afk_data.json"

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = self.load_afk_data()

    # === JSON Storage ===
    def load_afk_data(self):
        if not os.path.exists(AFK_FILE):
            return {}
        with open(AFK_FILE, "r") as f:
            data = json.load(f)
        for user_id, info in data.items():
            info["since"] = datetime.fromisoformat(info["since"])
        return data

    def save_afk_data(self):
        data = {
            str(uid): {
                "reason": d["reason"],
                "since": d["since"].isoformat()
            }
            for uid, d in self.afk_users.items()
        }
        with open(AFK_FILE, "w") as f:
            json.dump(data, f, indent=4)

    # === Time Formatting ===
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

    # === AFK Command ===
    @commands.command(name="afk")
    async def afk(self, ctx, *, reason: str = "AFK"):
        """Set yourself as AFK"""
        self.afk_users[ctx.author.id] = {
            "reason": reason,
            "since": datetime.now(timezone.utc)
        }
        self.save_afk_data()

        embed = discord.Embed(
            title="<:1000033723:1434107024265842748> AFK Activated",
            description=f"You are now AFK globally.\n**Reason:** {reason}",
            color=discord.Color.blurple()
        )
        await ctx.reply(embed=embed, mention_author=False)

    # === Listener for AFK Remove and Mentions ===
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return  # ignore commands

        # If AFK user sends message → remove AFK
        if message.author.id in self.afk_users:
            info = self.afk_users.pop(message.author.id)
            self.save_afk_data()

            afk_time = datetime.now(timezone.utc) - info["since"]
            duration = self.format_duration(afk_time)

            embed = discord.Embed(
                title="AFK Removed",
                description=f"Welcome back **{message.author.display_name}**!\nYou were AFK for **{duration}**.",
                color=discord.Color.green()
            )
            await message.reply(embed=embed, mention_author=False)
            return

        # If message mentions an AFK user
        for mention in message.mentions:
            if mention.id in self.afk_users:
                info = self.afk_users[mention.id]
                ago = self.format_ago(datetime.now(timezone.utc) - info["since"])
                reason = info["reason"]

                embed = discord.Embed(
                    description=f"**{mention.display_name}** is AFK: {reason} — {ago}.",
                    color=discord.Color.orange()
                )
                await message.channel.send(embed=embed)
                break  # Only respond for one AFK mention per message

async def setup(bot):
    await bot.add_cog(AFK(bot))