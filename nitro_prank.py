import discord
from discord.ext import commands
from discord import ui, ButtonStyle, Interaction

RICKROLL_GIF = "https://media3.giphy.com/media/v1.Y2lkPTZjMDliOTUyMW9veTF6Ym13aDN1a3pobzJld2xyaHh6Yjk3emQzZzRlcmM5b3p2dSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/g7GKcSzwQfugw/giphy.gif"

class NitroPrank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="nitro")
    async def nitro(self, ctx, target: discord.Member = None):
        """Send a fake Nitro gift that rickrolls the target."""
        target = target or ctx.author

        embed = discord.Embed(
            title="🎁 You've been gifted a Discord Nitro!",
            description=f"**{ctx.author.display_name}** has gifted you **1 Month of Discord Nitro**!\n\nClick the **Redeem** button to claim your gift.",
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/935532103487750184.webp?size=96&quality=lossless")
        embed.set_footer(text="This gift will expire in 48 hours.")

        class RedeemView(ui.View):
            def __init__(self, author_id: int, target_id: int):
                # 👇 Timeout set to 3600 seconds (1 hour)
                super().__init__(timeout=3600)
                self.author_id = author_id
                self.target_id = target_id
                self.redeemed = False

            @ui.button(label="Redeem", style=ButtonStyle.green)
            async def redeem(self, interaction: Interaction, button: ui.Button):
                if interaction.user.id not in (self.target_id, self.author_id):
                    return await interaction.response.send_message("❌ This gift isn’t for you!", ephemeral=True)

                if self.redeemed:
                    return await interaction.response.send_message("Already redeemed!", ephemeral=True)

                self.redeemed = True
                await interaction.response.send_message(
                    "🎉 Congratulations! You've been **rickrolled** 😂",
                    ephemeral=True
                )

                prank_embed = discord.Embed(
                    title="😂 You've Been Rickrolled!",
                    description=f"{interaction.user.mention} opened a **fake Nitro gift!**",
                    color=discord.Color.dark_theme()
                )
                prank_embed.set_image(url=RICKROLL_GIF)
                prank_embed.set_footer(text="Better luck next time!")

                await interaction.message.edit(embed=prank_embed, view=None)

        view = RedeemView(ctx.author.id, target.id)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(NitroPrank(bot))