import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Modal, TextInput


# ---------- Generic modal for input popups ----------

class EmbedInput(Modal):
    def __init__(self, title: str, labels: list[str], fields: list[str],
                 styles: list[discord.TextStyle], view):
        super().__init__(title=title)
        self.view_ref = view
        self.fields = fields
        for label, field, style in zip(labels, fields, styles):
            self.add_item(TextInput(label=label, style=style, required=False))

    async def on_submit(self, interaction: discord.Interaction):
        for text_input, field in zip(self.children, self.fields):
            value = text_input.value.strip() if text_input.value else None
            if not value:
                continue

            if field == "title":
                self.view_ref.embed.title = value
            elif field == "description":
                self.view_ref.embed.description = value
            elif field == "color":
                if value.startswith("#"):
                    value = value[1:]
                try:
                    self.view_ref.embed.color = discord.Color(int(value, 16))
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid color. Use a hex like `#00ff00`.",
                        ephemeral=True,
                    )
                    return
            elif field == "image":
                self.view_ref.embed.set_image(url=value)
            elif field == "thumbnail":
                self.view_ref.embed.set_thumbnail(url=value)

        await interaction.response.edit_message(embed=self.view_ref.embed, view=self.view_ref)


# ---------- Builder view ----------

class EmbedBuilder(View):
    def __init__(self, author_id: int, target_channel: discord.TextChannel = None, from_prefix: bool = False):
        super().__init__(timeout=1200)  # 20 min timeout
        self.author_id = author_id
        self.target_channel = target_channel
        self.from_prefix = from_prefix
        self.embed = discord.Embed(
            description="Use the buttons below to add fields",
            color=discord.Color.blurple(),
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "You can’t use this builder.", ephemeral=True
            )
            return False
        return True

    # ===== Buttons =====

    @discord.ui.button(label="Title", style=discord.ButtonStyle.primary)
    async def title_button(self, interaction, button):
        await interaction.response.send_modal(
            EmbedInput("Set Title", ["Enter the embed title"],
                       ["title"], [discord.TextStyle.short], self)
        )

    @discord.ui.button(label="Description", style=discord.ButtonStyle.primary)
    async def desc_button(self, interaction, button):
        await interaction.response.send_modal(
            EmbedInput("Set Description", ["Enter the embed description"],
                       ["description"], [discord.TextStyle.paragraph], self)
        )

    @discord.ui.button(label="Color", style=discord.ButtonStyle.primary)
    async def color_button(self, interaction, button):
        await interaction.response.send_modal(
            EmbedInput("Set Color", ["Enter color hex (e.g. #ff0000)"],
                       ["color"], [discord.TextStyle.short], self)
        )

    @discord.ui.button(label="Image", style=discord.ButtonStyle.secondary)
    async def image_button(self, interaction, button):
        await interaction.response.send_modal(
            EmbedInput("Set Image", ["Paste image URL"],
                       ["image"], [discord.TextStyle.short], self)
        )

    @discord.ui.button(label="Thumbnail", style=discord.ButtonStyle.secondary)
    async def thumb_button(self, interaction, button):
        await interaction.response.send_modal(
            EmbedInput("Set Thumbnail", ["Paste thumbnail URL"],
                       ["thumbnail"], [discord.TextStyle.short], self)
        )

    # ---------- Footer (auto-fill) ----------
    @discord.ui.button(label="Footer", style=discord.ButtonStyle.secondary)
    async def footer_button(self, interaction, button):
        view_ref = self

        class FooterModal(Modal, title="Set Footer"):
            footer_text = TextInput(
                label="Footer text (leave blank for auto)",
                style=discord.TextStyle.short,
                required=False
            )
            footer_icon = TextInput(
                label="Footer icon URL (optional)",
                style=discord.TextStyle.short,
                required=False
            )

            async def on_submit(self, inter):
                text = self.footer_text.value.strip() if self.footer_text.value else f"Created by {inter.user.name}"
                icon = self.footer_icon.value.strip() if self.footer_icon.value else inter.user.display_avatar.url
                view_ref.embed.set_footer(text=text, icon_url=icon)
                await inter.response.edit_message(embed=view_ref.embed, view=view_ref)

        await interaction.response.send_modal(FooterModal())

    # ---------- Finish / Exit ----------
    @discord.ui.button(label="Finish and Send", style=discord.ButtonStyle.success)
    async def save_button(self, interaction, button):
        if not self.target_channel:
            await interaction.response.send_message("⚠️ No channel selected!", ephemeral=True)
            return

        try:
            await self.target_channel.send(embed=self.embed)

            # If it's from slash -> edit ephemeral
            if not self.from_prefix:
                await interaction.response.edit_message(
                    content=f"✅ Embed sent successfully in {self.target_channel.mention}!",
                    embed=None,
                    view=None
                )
            else:
                # If it's from prefix -> delete builder
                await interaction.message.delete()

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don’t have permission to send in that channel.",
                ephemeral=True
            )

        self.stop()

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.danger)
    async def exit_button(self, interaction, button):
        if not self.from_prefix:
            await interaction.response.edit_message(
                content="❌ Builder closed.",
                embed=None,
                view=None
            )
        else:
            await interaction.message.delete()
        self.stop()


# ---------- Cog ----------

class EmbedBuilderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---- Prefix command ----
    @commands.command(name="embed")
    @commands.has_permissions(manage_messages=True)
    async def embed_prefix(self, ctx: commands.Context):
        """Create a custom embed (interactive builder)."""
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        view = EmbedBuilder(author_id=ctx.author.id, target_channel=ctx.channel, from_prefix=True)
        await ctx.send(embed=view.embed, view=view)

    # ---- Slash command ----
    @app_commands.command(
        name="embedbuilder",
        description="Create a custom embed and choose where to send it."
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(channel="Choose which channel to send the embed to")
    async def embed_slash(self, interaction: discord.Interaction, channel: discord.TextChannel):
        view = EmbedBuilder(author_id=interaction.user.id, target_channel=channel, from_prefix=False)
        await interaction.response.send_message(embed=view.embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(EmbedBuilderCog(bot))