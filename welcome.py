import discord
from discord.ext import commands

INVITE_LINK = "https://discord.gg/5Rf2uzY2gh"  # your support server link

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # Try to find a system or general channel
        channel = guild.system_channel or next(
            (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None
        )
        if not channel:
            return

        embed = discord.Embed(
            title="Thank you for adding Furina 💧",
            description=(
                "💧 **Furina is now in your server!**\n\n"
                "Default prefix: `,` (you can change it anytime using `,setprefix <new prefix>`)\n\n"
                "Use `,help` to see all commands and explore Furina's features!\n"
                "Ping **@Furina** anytime for assistance 💙"
            ),
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="💠 Need Help?",
            value=f"Join our [Official Server]({INVITE_LINK}) for support and updates!",
            inline=False
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="The Official Furina Bot Server", icon_url=self.bot.user.display_avatar.url)

        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))