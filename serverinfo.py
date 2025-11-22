import discord

from discord.ext import commands

class ServerInfo(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    @commands.command(name="serverinfo", aliases=["sinfo", "si"])

    async def serverinfo(self, ctx):

        guild = ctx.guild

        # --- Basic Info ---

        owner = guild.owner

        created_timestamp = int(guild.created_at.timestamp())

        boosts = guild.premium_subscription_count

        boost_tier = guild.premium_tier

        # --- Members ---

        total_members = guild.member_count

        humans = len([m for m in guild.members if not m.bot])

        bots = len([m for m in guild.members if m.bot])

        online = len([m for m in guild.members if m.status != discord.Status.offline])

        # --- Roles ---

        roles = guild.roles

        total_roles = len(roles)

        hoisted = len([r for r in roles if r.hoist])

        unhoisted = total_roles - hoisted

        # --- Emojis ---

        total_emojis = len(guild.emojis)

        animated = len([e for e in guild.emojis if e.animated])

        static = total_emojis - animated

        # --- Channels ---

        total_channels = len(guild.channels)

        text_channels = len(guild.text_channels)

        voice_channels = len(guild.voice_channels)

        categories = len(guild.categories)

        threads = sum(len(tc.threads) for tc in guild.text_channels)

        # --- Vanity ---

        vanity = guild.vanity_url_code or "None"

        # --- Embed ---

        embed = discord.Embed(

            title=guild.name,

            color=discord.Color.blurple()

        )

        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)

        embed.add_field(name="<:4b3c667823db4afe960a22f37b0a891b:1433184419899899996> Owner", value=f"{owner.mention}", inline=False)

        embed.add_field(name="<:1000033518:1433187121673539634> Created", value=f"<t:{created_timestamp}:D>", inline=False)

        embed.add_field(name="<:1000033519:1433187447944253521> Boosts", value=f"{boosts} (Level {boost_tier})", inline=False)

        embed.add_field(

            name="<:1000033517:1433185528739663974> Members",

            value=f"**Total:** {total_members}\n**Humans:** {humans}\n**Bots:** {bots}\n**Online:** {online}",

            inline=False

        )

        embed.add_field(

            name="<:1000033520:1433187962870304869> Roles",

            value=f"**Total:** {total_roles}\n**Hoisted:** {hoisted}\n**Unhoisted:** {unhoisted}",

            inline=False

        )

        embed.add_field(

            name="<:1000033521:1433189029289005116> Emojis",

            value=f"**Total:** {total_emojis}\n**Animated:** {animated}\n**Static:** {static}",

            inline=False

        )

        embed.add_field(name="<:1000033522:1433189442600046764> Vanity", value=f"{vanity}", inline=False)

        embed.add_field(

            name="<:1000033523:1433189677392728174> Channels",

            value=(

                f"**Total:** {total_channels}\n"

                f"**Text:** {text_channels}\n"

                f"**Voice:** {voice_channels}\n"

                f"**Categories:** {categories}\n"

                f"**Threads:** {threads}"

            ),

            inline=False

        )

        if guild.banner:

            embed.set_image(url=guild.banner.url)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):

    await bot.add_cog(ServerInfo(bot))