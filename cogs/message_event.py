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
        if message.author.bot:
            return

        bot_id = str(self.bot.user.id)

        if message.content.strip() in (f"<@{bot_id}>", f"<@!{bot_id}>"):
            uptime = datetime.now(timezone.utc) - self.start_time
            total_seconds = int(uptime.total_seconds())

            hrs, rem = divmod(total_seconds, 3600)
            mins, secs = divmod(rem, 60)

            if hrs:
                time_str = f"{hrs}h {mins}m"
            elif mins:
                time_str = f"{mins}m {secs}s"
            else:
                time_str = f"{secs}s"

            embed = discord.Embed(
                title=f"{self.bot.user.name} is here to help!",
                description=f"**Prefix:** ,\n**Uptime:** {time_str}\n💡 Use `,help` to see commands!",
                color=discord.Color.blurple()
            )

            if self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)

            embed.set_footer(
                text=f"Requested by {message.author}",
                icon_url=message.author.display_avatar.url
            )

            await message.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MessageEvent(bot))
