import discord
from discord.ext import commands


class AvatarView(discord.ui.LayoutView):
    def __init__(self, user: discord.User, member: discord.Member | None):
        super().__init__(timeout=60)
        self.user = user
        self.member = member
        self.mode = "avatar"
        self.build()

    def get_image_url(self):
        if self.mode == "avatar":
            return self.user.display_avatar.url
        if self.mode == "banner":
            return self.user.banner.url if self.user.banner else None
        if self.mode == "server" and self.member:
            return self.member.guild_avatar.url if self.member.guild_avatar else None
        return None

    def build(self):
        self.clear_items()
        image_url = self.get_image_url()

        container = discord.ui.Container(
            accent_color=discord.Color.blurple()
        )

        container.add_item(
            discord.ui.TextDisplay(
                f"**{self.user.name}'s {self.mode.capitalize()}**"
            )
        )

        container.add_item(discord.ui.Separator())

        if image_url:
            container.add_item(
                discord.ui.MediaGallery(
                    discord.MediaGalleryItem(image_url)
                )
            )
        else:
            container.add_item(
                discord.ui.TextDisplay("This image is not available.")
            )

        container.add_item(discord.ui.Separator())

        container.add_item(
            discord.ui.TextDisplay("**Switch view:**")
        )

        container.add_item(
            discord.ui.ActionRow(
                discord.ui.Button(
                    label="Avatar",
                    style=discord.ButtonStyle.primary,
                    custom_id="avatar",
                    disabled=self.mode == "avatar",
                ),
                discord.ui.Button(
                    label="Banner",
                    style=discord.ButtonStyle.secondary,
                    custom_id="banner",
                    disabled=self.mode == "banner" or not self.user.banner,
                ),
                discord.ui.Button(
                    label="Server",
                    style=discord.ButtonStyle.secondary,
                    custom_id="server",
                    disabled=not self.member or not self.member.guild_avatar,
                ),
            )
        )

        container.add_item(discord.ui.Separator())

        if image_url:
            container.add_item(
                discord.ui.ActionRow(
                    discord.ui.Button(
                        label="Open",
                        style=discord.ButtonStyle.link,
                        url=image_url,
                    ),
                    discord.ui.Button(
                        label="Download",
                        style=discord.ButtonStyle.link,
                        url=image_url + "?size=4096",
                    ),
                )
            )

        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        cid = interaction.data.get("custom_id")

        if cid in {"avatar", "banner", "server"}:
            self.mode = cid
            self.build()
            await interaction.response.edit_message(view=self)
            return True

        return False


class Avatar(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="pfp", aliases=["av", "avatar"])
    async def pfp(self, ctx: commands.Context, user: discord.User | None = None):
        """Show a user's avatar, banner, or server avatar."""
        user = user or ctx.author

        user = await self.bot.fetch_user(user.id)

        member = None
        if ctx.guild:
            member = ctx.guild.get_member(user.id)

        await ctx.send(
            view=AvatarView(user, member)
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Avatar(bot))
