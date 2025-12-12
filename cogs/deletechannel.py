import discord
from discord.ext import commands
from discord import app_commands

class ConfirmDelete(discord.ui.View):
    def __init__(self, author, channel, reason, cog):
        super().__init__(timeout=20)
        self.author = author
        self.channel = channel
        self.reason = reason
        self.cog = cog

    @discord.ui.button(label="Confirm Deletion", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                "Only the user who initiated this action can confirm it.",
                ephemeral=True
            )

        for child in self.children:
            child.disabled = True

        await interaction.message.edit(
            content=f"Channel **{self.channel.name}** has been deleted.",
            view=None
        )

        await self.channel.delete(reason=self.reason)

        await interaction.response.send_message(
            "Deletion completed.",
            ephemeral=True
        )

        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                "You cannot cancel this action.",
                ephemeral=True
            )

        for child in self.children:
            child.disabled = True

        await interaction.message.edit(
            content="Channel deletion has been cancelled.",
            view=None
        )

        await interaction.response.send_message(
            "Cancelled successfully.",
            ephemeral=True
        )

        self.stop()


class Delete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="delete")
    @commands.has_permissions(manage_channels=True)
    async def delete_prefix(self, ctx, channel: discord.TextChannel = None, *, reason=None):
        target = channel or ctx.channel

        if isinstance(target, discord.CategoryChannel):
            return await ctx.reply("Deleting categories is not supported using this command.")

        view = ConfirmDelete(ctx.author, target, reason, self)

        await ctx.reply(
            f"Are you sure you want to delete **{target.name}**?\n"
            "This action cannot be undone.",
            view=view
        )

    @app_commands.command(name="delete", description="Delete a channel from the server.")
    @app_commands.describe(
        channel="Channel to delete (leave empty to delete the current channel).",
        reason="Reason for deleting the channel."
    )
    async def delete_slash(self, interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = None):
        target = channel or interaction.channel

        if isinstance(target, discord.CategoryChannel):
            return await interaction.response.send_message(
                "Deleting categories is not supported using this command.",
                ephemeral=True
            )

        view = ConfirmDelete(interaction.user, target, reason, self)

        await interaction.response.send_message(
            f"Are you sure you want to delete **{target.name}**?\n"
            "This action is permanent.",
            view=view,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Delete(bot))
