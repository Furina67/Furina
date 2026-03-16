import discord
from discord.ext import commands
from datetime import datetime, timezone

class ServerInfoView(discord.ui.LayoutView):
    def __init__(self, guild: discord.Guild, author: discord.User):
        super().__init__(timeout=180)
        self.guild = guild
        self.author = author
        self.page = 0
        self.pages = self.build_pages()

        self.container = discord.ui.Container()
        self.add_item(self.container)

        self.update_page()

    def build_pages(self):
        guild = self.guild
        now = datetime.now(timezone.utc)

        owner_name = str(guild.owner) if guild.owner else "Unknown"
        created = int(guild.created_at.timestamp())

        total_members = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = total_members - humans
        online = len([m for m in guild.members if m.status != discord.Status.offline])

        total_roles = len(guild.roles)
        hoisted = len([r for r in guild.roles if r.hoist])
        managed = len([r for r in guild.roles if r.managed])

        total_emojis = len(guild.emojis)
        animated = len([e for e in guild.emojis if e.animated])

        total_channels = len(guild.channels)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        threads = sum(len(tc.threads) for tc in guild.text_channels)

        boosts = guild.premium_subscription_count
        boost_tier = guild.premium_tier

        vanity = guild.vanity_url_code or "None"

        days_old = (now - guild.created_at).days or 1
        growth_rate = round(total_members / days_old, 2)

        page1 = (
            f"**Owner:** {owner_name}\n"
            f"**Server ID:** `{guild.id}`\n"
            f"**Created:** <t:{created}:D>\n"
            f"**Vanity URL:** {vanity}\n"
            f"**Boosts:** {boosts} (Level {boost_tier})"
        )

        page2 = (
            f"**Total Members:** {total_members}\n"
            f"**Humans:** {humans}\n"
            f"**Bots:** {bots}\n"
            f"**Online:** {online}\n"
            f"**Estimated Growth:** ~{growth_rate} members/day"
        )

        page3 = (
            f"**Total Roles:** {total_roles}\n"
            f"**Hoisted Roles:** {hoisted}\n"
            f"**Managed Roles:** {managed}\n\n"
            f"**Total Emojis:** {total_emojis}\n"
            f"**Animated Emojis:** {animated}"
        )

        page4 = (
            f"**Total Channels:** {total_channels}\n"
            f"**Text Channels:** {text_channels}\n"
            f"**Voice Channels:** {voice_channels}\n"
            f"**Categories:** {categories}\n"
            f"**Threads:** {threads}"
        )

        return [page1, page2, page3, page4]

    def update_page(self):
        self.container.clear_items()

        text = discord.ui.TextDisplay(
            f"## {self.guild.name}\n\n{self.pages[self.page]}"
        )

        thumbnail = discord.ui.Thumbnail(
            media=self.guild.icon.url if self.guild.icon else None
        )

        section = discord.ui.Section(text, accessory=thumbnail)
        self.container.add_item(section)

        if self.guild.banner:
            gallery = discord.ui.MediaGallery(
                discord.MediaGalleryItem(self.guild.banner.url)
            )
            self.container.add_item(discord.ui.Separator())
            self.container.add_item(gallery)

        self.container.add_item(discord.ui.Separator())

        row = discord.ui.ActionRow()

        prev_btn = discord.ui.Button(label="Previous", style=discord.ButtonStyle.secondary)
        next_btn = discord.ui.Button(label="Next", style=discord.ButtonStyle.secondary)

        prev_btn.disabled = self.page == 0
        next_btn.disabled = self.page == len(self.pages) - 1

        async def prev_callback(interaction: discord.Interaction):
            if interaction.user != self.author:
                return await interaction.response.send_message("You cannot control this menu.", ephemeral=True)
            self.page -= 1
            self.update_page()
            await interaction.response.edit_message(view=self, allowed_mentions=discord.AllowedMentions.none())

        async def next_callback(interaction: discord.Interaction):
            if interaction.user != self.author:
                return await interaction.response.send_message("You cannot control this menu.", ephemeral=True)
            self.page += 1
            self.update_page()
            await interaction.response.edit_message(view=self, allowed_mentions=discord.AllowedMentions.none())

        prev_btn.callback = prev_callback
        next_btn.callback = next_callback

        row.add_item(prev_btn)
        row.add_item(next_btn)

        self.container.add_item(row)


class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="serverinfo", aliases=["sinfo", "si"])
    async def serverinfo(self, ctx):
        view = ServerInfoView(ctx.guild, ctx.author)
        await ctx.send(
            view=view,
            allowed_mentions=discord.AllowedMentions.none()
        )


async def setup(bot):
    await bot.add_cog(ServerInfo(bot))