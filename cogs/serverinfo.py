import discord
from discord.ext import commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="serverinfo", aliases=["sinfo", "si"])
    async def serverinfo(self, ctx):
        guild = ctx.guild

        owner = guild.owner
        created_ts = int(guild.created_at.timestamp())

        boosts = guild.premium_subscription_count
        boost_tier = guild.premium_tier

        total_members = guild.member_count
        humans = sum(not m.bot for m in guild.members)
        bots = sum(m.bot for m in guild.members)
        online = sum(m.status != discord.Status.offline for m in guild.members)

        roles = guild.roles
        total_roles = len(roles)
        hoisted = sum(r.hoist for r in roles)

        total_emojis = len(guild.emojis)
        animated = sum(e.animated for e in guild.emojis)

        total_channels = len(guild.channels)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        threads = sum(len(c.threads) for c in guild.text_channels)

        vanity = guild.vanity_url_code or "None"

        embed = discord.Embed(
            title=guild.name,
            color=discord.Color.blurple()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="Owner", value=owner.mention, inline=False)
        embed.add_field(name="Created", value=f"<t:{created_ts}:D>", inline=False)
        embed.add_field(name="Boosts", value=f"{boosts} (Level {boost_tier})", inline=False)

        embed.add_field(
            name="Members",
            value=(
                f"Total: {total_members}\n"
                f"Humans: {humans}\n"
                f"Bots: {bots}\n"
                f"Online: {online}"
            ),
            inline=False
        )

        embed.add_field(
            name="Roles",
            value=(
                f"Total: {total_roles}\n"
                f"Hoisted: {hoisted}\n"
                f"Unhoisted: {total_roles - hoisted}"
            ),
            inline=False
        )

        embed.add_field(
            name="Emojis",
            value=(
                f"Total: {total_emojis}\n"
                f"Animated: {animated}\n"
                f"Static: {total_emojis - animated}"
            ),
            inline=False
        )

        embed.add_field(
            name="Channels",
            value=(
                f"Total: {total_channels}\n"
                f"Text: {text_channels}\n"
                f"Voice: {voice_channels}\n"
                f"Categories: {categories}\n"
                f"Threads: {threads}"
            ),
            inline=False
        )

        embed.add_field(name="Vanity", value=vanity, inline=False)

        if guild.banner:
            embed.set_image(url=guild.banner.url)

        embed.set_footer(
            text=f"Requested by {ctx.author}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))
