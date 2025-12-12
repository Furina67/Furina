import discord
from discord.ext import commands
import random

class MinesButton(discord.ui.Button):
    def __init__(self, x, y, is_mine):
        super().__init__(style=discord.ButtonStyle.secondary, label="⬛", row=y)
        self.x = x
        self.y = y
        self.is_mine = is_mine
        self.revealed = False

    async def callback(self, interaction: discord.Interaction):
        view: MinesView = self.view

        if view.game_over:
            return await interaction.response.send_message("💥 Game over already!", ephemeral=True)

        if self.revealed:
            return await interaction.response.send_message("⛏️ You already opened this spot!", ephemeral=True)

        self.revealed = True

        if self.is_mine:
            self.style = discord.ButtonStyle.danger
            self.label = "💣"
            view.game_over = True

            for child in view.children:
                if isinstance(child, MinesButton) and child.is_mine:
                    child.label = "💣"
                    child.style = discord.ButtonStyle.danger

            return await interaction.response.edit_message(
                content="💥 **Boom! You hit a mine!**",
                view=view
            )

        self.style = discord.ButtonStyle.success
        self.label = "💎"
        view.safe_reveals += 1

        if view.safe_reveals == view.total_safe:
            view.game_over = True
            return await interaction.response.edit_message(
                content="🎉 **You cleared all safe spots! You win!**",
                view=view
            )

        await interaction.response.edit_message(view=view)


class MinesView(discord.ui.View):
    def __init__(self, size=5, mines=5):
        super().__init__(timeout=120)
        self.size = size
        self.mines = mines
        self.game_over = False
        self.safe_reveals = 0
        self.total_safe = size * size - mines

        positions = [(x, y) for x in range(size) for y in range(size)]
        mine_positions = random.sample(positions, mines)

        for x, y in positions:
            self.add_item(MinesButton(x, y, (x, y) in mine_positions))


class Mines(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="mines")
    async def mines(self, ctx, mines: int = 5):
        if not (1 <= mines <= 10):
            return await ctx.send("⚠️ You can only have between 1 and 10 mines!")

        view = MinesView(size=5, mines=mines)

        embed = discord.Embed(
            title="💣 Mines Game",
            description=f"Click the squares to avoid mines!\n**Mines:** {mines}",
            color=discord.Color.blurple()
        )
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Mines(bot))
