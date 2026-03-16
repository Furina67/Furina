import discord
from discord.ext import commands
from datetime import datetime, timezone
import json
import os

PREFIX_FILE = "prefixes.json"
DEFAULT_PREFIX = ","


def get_prefix(guild_id: int) -> str:
    if not os.path.exists(PREFIX_FILE):
        return DEFAULT_PREFIX

    with open(PREFIX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get(str(guild_id), DEFAULT_PREFIX)


class BotMentionView(discord.ui.LayoutView):
    def __init__(
        self,
        bot: commands.Bot,
        author: discord.User,
        guild: discord.Guild,
        prefix: str,
        uptime: str,
    ):
        super().__init__(timeout=60)

        container = discord.ui.Container(
            accent_color=discord.Color.blue()
        )

        container.add_item(
            discord.ui.Section(
                discord.ui.TextDisplay(
                    f"**{bot.user.name}**\n\n"
                    f"Hey {author.mention},\n"
                    f"Prefix for this server is `{prefix}`\n\n"
                    f"**Server ID:** `{guild.id}`\n"
                    f"**Uptime:** `{uptime}`\n\n"
                    f"Type `{prefix}help` for more information"
                ),
                accessory=discord.ui.Thumbnail(
                    media=bot.user.display_avatar.url
                )
            )
        )

        container.add_item(discord.ui.Separator())

        container.add_item(
            discord.ui.ActionRow(
                discord.ui.Button(
                    label="Add Me",
                    style=discord.ButtonStyle.link,
                    url="https://discord.com/oauth2/authorize?client_id=1423421449028239370"
                ),
                discord.ui.Button(
                    label="Support",
                    style=discord.ButtonStyle.link,
                    url="https://discord.gg/xwW6t7T3WZ"
                ),
            )
        )

        self.add_item(container)


class MessageEvent(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.now(timezone.utc)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if message.content.strip() not in (
            f"<@{self.bot.user.id}>",
            f"<@!{self.bot.user.id}>",
        ):
            return

        delta = datetime.now(timezone.utc) - self.start_time
        seconds = int(delta.total_seconds())

        if seconds < 60:
            uptime = f"{seconds}s"
        elif seconds < 3600:
            uptime = f"{seconds // 60}m"
        else:
            uptime = f"{seconds // 3600}h {(seconds % 3600) // 60}m"

        prefix = get_prefix(message.guild.id)
        ctx = await self.bot.get_context(message)

        await ctx.send(
            view=BotMentionView(
                bot=self.bot,
                author=message.author,
                guild=message.guild,
                prefix=prefix,
                uptime=uptime,
            ),
            allowed_mentions=discord.AllowedMentions(users=False),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(MessageEvent(bot))