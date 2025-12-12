import discord
from discord.ext import commands
import json
import os

DATA_FILE = "counting_data.json"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def counting(self, ctx, channel: discord.TextChannel):
        self.data[str(ctx.guild.id)] = {
            "channel": channel.id,
            "last_number": 0,
            "last_user": None
        }
        save_data(self.data)
        await ctx.send(f"Counting channel set to {channel.mention}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        if guild_id not in self.data:
            return

        channel_id = self.data[guild_id]["channel"]
        if message.channel.id != channel_id:
            return

        try:
            number = int(message.content.strip())
        except ValueError:
            await message.delete()
            return

        last_number = self.data[guild_id]["last_number"]
        last_user = self.data[guild_id]["last_user"]

        if number == last_number + 1:
            if message.author.id == last_user and last_number != 0:
                await message.delete()
                warn = await message.channel.send("You cannot count twice in a row.")
                await warn.delete(delay=5)
                return

            self.data[guild_id]["last_number"] = number
            self.data[guild_id]["last_user"] = message.author.id
            save_data(self.data)
            await message.add_reaction("✅")

        else:
            await message.delete()
            wrong = await message.channel.send(
                f"Wrong number. The next number should be **{last_number + 1}**."
            )
            await wrong.delete(delay=5)


async def setup(bot):
    await bot.add_cog(Counting(bot))
