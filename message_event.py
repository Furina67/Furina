# cogs/message_event.py

import discord
from discord.ext import commands
from datetime import datetime, timezone
import re

class MessageEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mention_pattern = re.compile(r"<@!?(\d+)>")
        self.start_time = datetime.now(timezone.utc)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages
        if message.author.bot:
            return

        # --- Bot mention reply ---
        if message.content.strip() in [f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>"]:
            uptime = datetime.now(timezone.utc) - self.start_time
            mins, secs = divmod(int(uptime.total_seconds()), 60)
            hrs, mins = divmod(mins, 60)

            time_str = (
                f"{hrs}h {mins}m"
                if hrs
                else f"{mins}m {secs}s"
                if mins
                else f"{secs}s"
            )

            embed = discord.Embed(
                title=f"{self.bot.user.name} is here to help!",
                description=f"**Prefix:** ,\n**Uptime:** {time_str}\n💡 Use `,help` to see commands!",
                color=discord.Color.blurple()
            )

            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.set_footer(
                text=f"Requested by {message.author}",
                icon_url=message.author.display_avatar.url
            )

            await message.channel.send(embed=embed)

# --- Setup function for load_extension ---
async def setup(bot):
    await bot.add_cog(MessageEvent(bot))