import discord
from discord.ext import commands
from discord.ui import View, Button

class TicTacToeButton(Button):
    def __init__(self, x, y):
        super().__init__(label="‎", style=discord.ButtonStyle.secondary, row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToe = self.view
        if interaction.user != view.current_player:
            return await interaction.response.send_message("It's not your turn!", ephemeral=True)

        if self.label != "‎":
            return await interaction.response.send_message("That spot is already taken!", ephemeral=True)

        self.label = view.symbols[view.current_player]
        self.style = discord.ButtonStyle.success if view.current_player == view.player1 else discord.ButtonStyle.danger
        self.disabled = True
        view.board[self.y][self.x] = view.symbols[view.current_player]

        winner = view.check_winner()
        if winner:
            for item in view.children:
                item.disabled = True
            await interaction.response.edit_message(content=f"<a:1000033704:1433945543746261054> {winner.mention} wins!", view=view)
            view.stop()
        elif view.is_draw():
            for item in view.children:
                item.disabled = True
            await interaction.response.edit_message(content="It's a draw!", view=view)
            view.stop()
        else:
            view.switch_turn()
            await interaction.response.edit_message(content=f"It's now {view.current_player.mention}'s turn!", view=view)


class TicTacToe(View):
    def __init__(self, player1, player2):
        super().__init__(timeout=300)  # 5-minute timeout
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.symbols = {player1: "❌", player2: "⭕"}
        self.board = [["‎"] * 3 for _ in range(3)]

        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def switch_turn(self):
        self.current_player = self.player1 if self.current_player == self.player2 else self.player2

    def check_winner(self):
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != "‎":
                return self.get_player_by_symbol(self.board[i][0])
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != "‎":
                return self.get_player_by_symbol(self.board[0][i])
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != "‎":
            return self.get_player_by_symbol(self.board[0][0])
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != "‎":
            return self.get_player_by_symbol(self.board[0][2])
        return None

    def is_draw(self):
        return all(cell != "‎" for row in self.board for cell in row)

    def get_player_by_symbol(self, symbol):
        for player, sym in self.symbols.items():
            if sym == symbol:
                return player

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(content="<:1000033665:1433771296554094705> Game timed out due to inactivity!", view=self)


class ChallengeView(View):
    def __init__(self, ctx, opponent):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.opponent = opponent
        self.message = None

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.opponent:
            return await interaction.response.send_message("You're not the challenged player!", ephemeral=True)
        self.stop()
        await interaction.message.delete()

        view = TicTacToe(self.ctx.author, self.opponent)
        game_msg = await self.ctx.send(
            f"{self.ctx.author.mention} vs {self.opponent.mention} — Game start!\nIt's {self.ctx.author.mention}'s turn!",
            view=view
        )
        view.message = game_msg

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.opponent:
            return await interaction.response.send_message("You're not the challenged player!", ephemeral=True)
        self.stop()
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="❌ Challenge Rejected",
                description=f"{self.opponent.mention} has declined the Tic Tac Toe challenge.",
                color=discord.Color.red()
            ),
            view=self
        )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(
                embed=discord.Embed(
                    title="<:1000033665:1433771296554094705> Challenge Timed Out",
                    description=f"{self.opponent.mention} didn’t respond in time.",
                    color=discord.Color.orange()
                ),
                view=self
            )


class TicTacToeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tictactoe", aliases=["ttt"])
    async def tictactoe(self, ctx, opponent: discord.Member):
        if opponent == ctx.author:
            return await ctx.reply("You can’t play against yourself!", mention_author=False)
        if opponent.bot:
            return await ctx.reply("You can’t challenge a bot!", mention_author=False)

        embed = discord.Embed(
            title="<a:1000033695:1433928688914792448> Tic Tac Toe Challenge",
            description=f"{ctx.author.mention} has challenged {opponent.mention} to a game of Tic Tac Toe!\nDo you accept?",
            color=discord.Color.blurple()
        )

        view = ChallengeView(ctx, opponent)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

async def setup(bot):
    await bot.add_cog(TicTacToeCog(bot))