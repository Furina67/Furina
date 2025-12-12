import discord
from discord.ext import commands
import asyncio
import json
import os

PREFIX_FILE = "prefixes.json"

if not os.path.exists(PREFIX_FILE):
    with open(PREFIX_FILE, "w") as f:
        json.dump({}, f)

def get_prefix(bot, message):
    """Fetch prefix for each server."""
    if not message.guild:
        return ","
    with open(PREFIX_FILE, "r") as f:
        prefixes = json.load(f)
    return prefixes.get(str(message.guild.id), ",")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

async def load_cogs():
    extensions = [
        "cogs.afk",
        "cogs.message_event",
        "cogs.help_menu",
        "cogs.snipe",
        "cogs.purge",
        "cogs.avatar",
        "cogs.calc",
        "cogs.membercount",
        "cogs.serverinfo",
        "cogs.ping",
        "cogs.mines",
        "cogs.blackjack",
        "cogs.coinflip",
        "cogs.waifu",
        "cogs.husbando",
        "cogs.accage",
        "cogs.meme_autopost",
        "cogs.giveaway",
        "cogs.nitro_prank",
        "cogs.checkvanity",
        "cogs.define",
        "cogs.moderation",
        "cogs.utility",
        "cogs.vanitysetup",
        "cogs.prefix_system",
        "cogs.nuke",
        "cogs.embed_builder",
        "cogs.say",
        "cogs.tictactoe",
        "cogs.server",
        "cogs.React",
        "cogs.counting",
        "cogs.ship",
        "cogs.tip",
        "cogs.claimtime",
        "cogs.giveaway_config",
        "cogs.leaveserver",
        "cogs.vote",
        "cogs.welcome",
        "cogs.rps",
        "cogs.steal",
        "cogs.crypto",
        "cogs.Wiki",
        "cogs.delete2",
        "cogs.chess",
        "cogs.ai",
        "cogs.welcomecmd",
    ]

    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded: {ext}")
        except Exception as e:
            print(f"❌ Failed: {ext} — {e}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Synced slash commands for {bot.user}")
    print(f"Furina is online — {bot.user} (ID: {bot.user.id})")

async def main():
    async with bot:
        await load_cogs()
        await bot.start("YOUR_TOKEN_HERE")

if __name__ == "__main__":
    asyncio.run(main())
