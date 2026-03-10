import discord
from discord.ext import commands


class AvatarView(discord.ui.LayoutView):
    def __init__(self, user_id: int, guild_id: int | None, author_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.guild_id = guild_id
        self.author_id = author_id
        self.mode = "avatar"

    async def build(self, bot: commands.Bot):
        self.clear_items()

        user = await bot.fetch_user(self.user_id)
        guild = bot.get_guild(self.guild_id) if self.guild_id else None
        member = guild.get_member(self.user_id) if guild else None

        image_url = None

        if self.mode == "avatar":
            image_url = user.display_avatar.url

        elif self.mode == "banner":
            image_url = user.banner.url if user.banner else None

        elif self.mode == "server_avatar" and member:
            image_url = member.guild_avatar.url if member.guild_avatar else None

        elif self.mode == "server_banner" and member:
            image_url = member.guild_banner.url if member.guild_banner else None

        container = discord.ui.Container()

        container.add_item(
            discord.ui.TextDisplay(
                f"## {user.name}'s {self.mode.replace('_', ' ').title()}"
            )
        )

        container.add_item(discord.ui.Separator())

        if image_url:
            gallery = discord.ui.MediaGallery()
            gallery.add_item(media=image_url)
            container.add_item(gallery)
        else:
            container.add_item(
                discord.ui.TextDisplay("This image is not available.")
            )

        container.add_item(discord.ui.Separator())

        switch_row = discord.ui.ActionRow()

        switch_row.add_item(discord.ui.Button(
            label="Avatar",
            style=discord.ButtonStyle.primary if self.mode == "avatar" else discord.ButtonStyle.secondary,
            custom_id=f"avatar:{self.user_id}:{self.guild_id}"
        ))

        switch_row.add_item(discord.ui.Button(
            label="Banner",
            style=discord.ButtonStyle.primary if self.mode == "banner" else discord.ButtonStyle.secondary,
            custom_id=f"banner:{self.user_id}:{self.guild_id}",
            disabled=not user.banner
        ))

        switch_row.add_item(discord.ui.Button(
            label="Server Avatar",
            style=discord.ButtonStyle.primary if self.mode == "server_avatar" else discord.ButtonStyle.secondary,
            custom_id=f"server_avatar:{self.user_id}:{self.guild_id}",
            disabled=not member or not member.guild_avatar
        ))

        switch_row.add_item(discord.ui.Button(
            label="Server Banner",
            style=discord.ButtonStyle.primary if self.mode == "server_banner" else discord.ButtonStyle.secondary,
            custom_id=f"server_banner:{self.user_id}:{self.guild_id}",
            disabled=not member or not member.guild_banner
        ))

        container.add_item(switch_row)

        if image_url:
            container.add_item(discord.ui.Separator())

            link_row = discord.ui.ActionRow()

            link_row.add_item(discord.ui.Button(
                label="Open",
                style=discord.ButtonStyle.link,
                url=image_url
            ))

            link_row.add_item(discord.ui.Button(
                label="Download",
                style=discord.ButtonStyle.link,
                url=image_url + "?size=4096"
            ))

            container.add_item(link_row)

        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "You cannot use this interaction.",
                ephemeral=True
            )
            return False

        cid = interaction.data.get("custom_id")
        if not cid:
            return False

        mode, user_id, guild_id = cid.split(":")
        self.mode = mode
        self.user_id = int(user_id)
        self.guild_id = None if guild_id == "None" else int(guild_id)

        await self.build(interaction.client)
        await interaction.response.edit_message(view=self)
        return True


class Avatar(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(AvatarView(0, None, 0))

    @commands.hybrid_command(
        name="avatar",
        description="View avatar, banner, server avatar or server banner", aliases=["pfp", "av"]
    )
    async def avatar(self, ctx: commands.Context, user: discord.User | None = None):
        user = user or ctx.author

        view = AvatarView(
            user.id,
            ctx.guild.id if ctx.guild else None,
            ctx.author.id
        )

        await view.build(self.bot)

        if ctx.interaction:
            await ctx.interaction.response.send_message(view=view)
        else:
            await ctx.send(view=view)


async def setup(bot):
    await bot.add_cog(Avatar(bot))