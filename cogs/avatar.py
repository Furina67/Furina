import discord
from discord.ext import commands

class AvatarView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=60)
        self.user = user
        self.showing_avatar = True

    async def update_embed(self, interaction: discord.Interaction, show_avatar: bool):
        if show_avatar == self.showing_avatar:
            await interaction.response.send_message(
                f"You're already viewing the {'avatar' if show_avatar else 'banner'}.",
                ephemeral=True
            )
            return

        self.showing_avatar = show_avatar
        embed = discord.Embed(
            title=f"{self.user.name}'s {'Avatar' if show_avatar else 'Banner'}",
            color=discord.Color.blurple()
        )

        if show_avatar:
            embed.set_image(url=self.user.display_avatar.url)
        elif self.user.banner:
            embed.set_image(url=self.user.banner.url)
        else:
            embed.description = "This user has no banner."

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Avatar", style=discord.ButtonStyle.primary)
    async def avatar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, True)

    @discord.ui.button(label="Banner", style=discord.ButtonStyle.secondary)
    async def banner_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, False)


class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="avatar", aliases=["av", "pfp", "banner"])
    async def avatar(self, ctx, user: discord.User = None):
        user = user or ctx.author
        user = await self.bot.fetch_user(user.id)

        embed = discord.Embed(
            title=f"{user.name}'s Avatar",
            color=discord.Color.blurple()
        )
        embed.set_image(url=user.display_avatar.url)
        embed.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(embed=embed, view=AvatarView(user))


async def setup(bot):
    await bot.add_cog(Avatar(bot))
