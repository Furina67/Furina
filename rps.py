import discord
from discord.ext import commands
import asyncio

class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def rps(self, ctx, opponent: discord.Member = None):
        CONTROLLER = "<a:1000033695:1433928688914792448>"
        TICK = "<a:1000033630:1433575320782372995>"
        BOT_EMOJI = "<:1000033758:1434606580363559045>"
        WRONG = "<:1000033789:1434817396308312064>"

        if not opponent:
            return await ctx.send(f"{WRONG} You must mention someone to challenge! Example: `,rps @user`")

        if opponent == ctx.author:
            return await ctx.send(f"{WRONG} You can't challenge yourself 💀")

        if opponent.bot:
            return await ctx.send(f"{BOT_EMOJI} You can't challenge a bot!")

        embed = discord.Embed(
            title=f"{CONTROLLER} Rock Paper Scissors Challenge",
            description=f"{ctx.author.mention} has challenged {opponent.mention} to a game of Rock Paper Scissors!\n\nDo you accept?",
            color=discord.Color.blurple()
        )

        view = AcceptView(ctx, opponent)
        message = await ctx.send(embed=embed, view=view)
        view.message = message


class AcceptView(discord.ui.View):
    def __init__(self, ctx, opponent):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.opponent = opponent
        self.message = None

    async def on_timeout(self):
        CONTROLLER = "<a:1000033695:1433928688914792448>"
        embed = discord.Embed(
            title=f"{CONTROLLER} Rock Paper Scissors Challenge",
            description="Challenge timed out. No response from opponent.",
            color=discord.Color.blurple()
        )
        await self.message.edit(embed=embed, view=None)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.opponent:
            await interaction.response.send_message("This isn't your challenge!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        CONTROLLER = "<a:1000033695:1433928688914792448>"

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        embed = discord.Embed(
            title=f"{CONTROLLER} Rock Paper Scissors Game",
            description="Each player selects their choice by clicking a button!",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Player 1", value=f"{self.ctx.author.mention}", inline=False)
        embed.add_field(name="Player 2", value=f"{self.opponent.mention}", inline=False)
        embed.set_footer(text="Waiting for both players to choose...")

        view = RPSButtons(self.ctx.author, self.opponent)
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = await interaction.original_response()
        view.ctx = self.ctx

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        CONTROLLER = "<a:1000033695:1433928688914792448>"
        WRONG = "<:1000033789:1434817396308312064>"

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        embed = discord.Embed(
            title=f"{CONTROLLER} Rock Paper Scissors Challenge",
            description=f"{interaction.user.mention} declined the challenge. {WRONG}",
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed)


class RPSButtons(discord.ui.View):
    def __init__(self, player1, player2):
        super().__init__(timeout=90)
        self.player1 = player1
        self.player2 = player2
        self.choices = {}
        self.message = None
        self.ctx = None

    async def on_timeout(self):
        CONTROLLER = "<a:1000033695:1433928688914792448>"
        embed = discord.Embed(
            title=f"{CONTROLLER} Rock Paper Scissors Game",
            description="Game timed out. One or both players didn't choose in time.",
            color=discord.Color.blurple()
        )
        await self.message.edit(embed=embed, view=None)

    async def disable_all(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def handle_choice(self, interaction, choice):
        if interaction.user not in [self.player1, self.player2]:
            return await interaction.response.send_message("You are not part of this game!", ephemeral=True)

        if interaction.user.id in self.choices:
            return await interaction.response.send_message("You already chose!", ephemeral=True)

        self.choices[interaction.user.id] = choice
        await interaction.response.defer()
        await self.update_embed()

        # Both chosen? -> show result
        if len(self.choices) == 2:
            await asyncio.sleep(1)
            await self.show_result()

    async def update_embed(self):
        CONTROLLER = "<a:1000033695:1433928688914792448>"
        embed = discord.Embed(
            title=f"{CONTROLLER} Rock Paper Scissors Game",
            description="Each player selects their choice by clicking a button!",
            color=discord.Color.blurple()
        )

        def status(p):
            return "✅ Chosen" if p.id in self.choices else "Waiting..."

        embed.add_field(name="Player 1", value=f"{self.player1.mention} - {status(self.player1)}", inline=False)
        embed.add_field(name="Player 2", value=f"{self.player2.mention} - {status(self.player2)}", inline=False)

        waiting = [p for p in [self.player1, self.player2] if p.id not in self.choices]
        if waiting:
            embed.set_footer(text=f"Waiting for {waiting[0].display_name} to choose...")
        else:
            embed.set_footer(text="Both players have chosen!")

        if self.message:
            await self.message.edit(embed=embed, view=self)

    async def show_result(self):
        await self.disable_all()

        CONTROLLER = "<a:1000033695:1433928688914792448>"
        TICK = "<a:1000033630:1433575320782372995>"

        choice_emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

        p1_choice = self.choices[self.player1.id]
        p2_choice = self.choices[self.player2.id]
        result = self.determine_winner(p1_choice, p2_choice)

        if result == 0:
            outcome = "🤝 It's a Tie!"
        elif result == 1:
            outcome = f"{TICK} {self.player1.mention} wins!"
        else:
            outcome = f"{TICK} {self.player2.mention} wins!"

        embed = discord.Embed(
            title=f"{CONTROLLER} Rock Paper Scissors Results",
            description="🎮 The game has ended!",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="Choices",
            value=f"{self.player1.mention} chose {choice_emojis[p1_choice]}  |  {self.player2.mention} chose {choice_emojis[p2_choice]}",
            inline=False
        )
        embed.add_field(name="Result", value=outcome, inline=False)
        embed.set_footer(text="Game Over! 🎉")

        if self.message:
            await self.message.edit(embed=embed, view=None)

    def determine_winner(self, p1, p2):
        if p1 == p2:
            return 0
        elif (p1 == "rock" and p2 == "scissors") or \
             (p1 == "paper" and p2 == "rock") or \
             (p1 == "scissors" and p2 == "paper"):
            return 1
        else:
            return 2

    @discord.ui.button(label="Rock", emoji="🪨", style=discord.ButtonStyle.primary)
    async def rock(self, interaction, button):
        await self.handle_choice(interaction, "rock")

    @discord.ui.button(label="Paper", emoji="📄", style=discord.ButtonStyle.success)
    async def paper(self, interaction, button):
        await self.handle_choice(interaction, "paper")

    @discord.ui.button(label="Scissors", emoji="✂️", style=discord.ButtonStyle.danger)
    async def scissors(self, interaction, button):
        await self.handle_choice(interaction, "scissors")


async def setup(bot):
    await bot.add_cog(RPS(bot))