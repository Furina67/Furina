import discord
from discord.ext import commands
from discord.ui import View, Button


class ConfirmNuke(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You can’t use this button.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        self.value = True
        await interaction.response.edit_message(content="💣 Nuking channel...", view=None)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        self.value = False
        await interaction.response.edit_message(content="❌ Nuke cancelled.", view=None)
        self.stop()


class Nuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="nuke")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def nuke(self, ctx: commands.Context):
        """Deletes and clones the current channel."""
        channel = ctx.channel

        guild = ctx.guild
        community_channels = {
            guild.rules_channel,
            guild.public_updates_channel,
            guild.system_channel,
        }

        if channel in community_channels:
            embed = discord.Embed(
                title="🚫 Can't Nuke This Channel",
                description="This channel is required for community servers and cannot be deleted.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title="⚠️ Confirm Channel Nuke",
            description="This will **delete all messages** and clone this channel.\nAre you sure you want to continue?",
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        view = ConfirmNuke(author_id=ctx.author.id)
        await ctx.send(embed=embed, view=view)

        await view.wait()

        if view.value is None:
            return await ctx.send("⌛ Nuke cancelled — no response after 60 seconds.")
        if view.value is False:
            return 

        try:
            new_channel = await channel.clone(reason=f"Nuked by {ctx.author}")
            await new_channel.edit(position=channel.position)
            await channel.delete()

            embed_done = discord.Embed(
                title="💥 Channel Nuked",
                description=f"{new_channel.mention} has been nuked successfully!",
                color=discord.Color.red()
            )
            embed_done.set_footer(text=f"Nuked by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await new_channel.send(embed=embed_done)

        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to manage channels.")
        except discord.HTTPException as e:
            if e.code == 50074:
                await ctx.send("🚫 This channel is required for community servers and cannot be deleted.")
            else:
                await ctx.send(f"❌ Unexpected error: `{e}`")
        except Exception as e:
            await ctx.send(f"❌ Something went wrong: `{e}`")


async def setup(bot):
    await bot.add_cog(Nuke(bot))
