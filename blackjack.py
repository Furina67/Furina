import discord

from discord.ext import commands

import random

class Blackjack(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    @commands.command(name="bj",aliases=["blackjack"])

    async def blackjack(self, ctx):

        suits = ["♠️", "♥️", "♦️", "♣️"]

        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

        def draw_card():

            return random.choice(ranks), random.choice(suits)

        def card_value(rank):

            if rank in ["J", "Q", "K"]:

                return 10

            elif rank == "A":

                return 11

            else:

                return int(rank)

        def calculate_hand_value(hand):

            value = sum(card_value(r) for r, _ in hand)

            aces = [r for r, _ in hand if r == "A"]

            while value > 21 and aces:

                value -= 10

                aces.pop()

            return value

        def format_hand(hand):

            return " ".join([f"{r}{s}" for r, s in hand])

        player_hand = [draw_card(), draw_card()]

        dealer_hand = [draw_card(), draw_card()]

        embed = discord.Embed(title="<:1000033530:1433199640760684554> Blackjack", color=discord.Color.blurple())

        embed.add_field(

            name="🧍 Your Hand",

            value=f"{format_hand(player_hand)}\n**Value:** {calculate_hand_value(player_hand)}",

            inline=False

        )

        embed.add_field(

            name="🏦 Dealer's Hand",

            value=f"{dealer_hand[0][0]}{dealer_hand[0][1]} ❓",

            inline=False

        )

        message = await ctx.send(embed=embed)

        class BlackjackView(discord.ui.View):

            def __init__(self):

                super().__init__()

            @discord.ui.button(label="Hit", style=discord.ButtonStyle.green, emoji="🃏")

            async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):

                if interaction.user != ctx.author:

                    return await interaction.response.send_message("❌ This isn’t your game!", ephemeral=True)

                player_hand.append(draw_card())

                player_value = calculate_hand_value(player_hand)

                embed.set_field_at(

                    0,

                    name="🧍 Your Hand",

                    value=f"{format_hand(player_hand)}\n**Value:** {player_value}",

                    inline=False,

                )

                await interaction.response.edit_message(embed=embed, view=self)

                if player_value > 21:

                    embed.title = "<:1000033528:1433199141395370145> You Busted!"

                    embed.color = discord.Color.red()

                    embed.set_field_at(

                        1,

                        name="🏦 Dealer's Hand",

                        value=f"{format_hand(dealer_hand)}\n**Value:** {calculate_hand_value(dealer_hand)}",

                        inline=False,

                    )

                    await interaction.message.edit(embed=embed, view=None)

            @discord.ui.button(label="Stand", style=discord.ButtonStyle.red, emoji="✋")

            async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):

                if interaction.user != ctx.author:

                    return await interaction.response.send_message("❌ This isn’t your game!", ephemeral=True)

                player_value = calculate_hand_value(player_hand)

                dealer_value = calculate_hand_value(dealer_hand)

                while dealer_value < 17:

                    dealer_hand.append(draw_card())

                    dealer_value = calculate_hand_value(dealer_hand)

                embed.set_field_at(

                    1,

                    name="🏦 Dealer's Hand",

                    value=f"{format_hand(dealer_hand)}\n**Value:** {dealer_value}",

                    inline=False,

                )

                if dealer_value > 21 or player_value > dealer_value:

                    embed.title = "<:1000033529:1433199457624784947> You Win!"

                    embed.color = discord.Color.green()

                elif player_value == dealer_value:

                    embed.title = "🤝 It's a Tie!"

                    embed.color = discord.Color.blurple()

                else:

                    embed.title = "<:1000033528:1433199141395370145> Dealer Wins!"

                    embed.color = discord.Color.red()

                await interaction.response.edit_message(embed=embed, view=None)

        await message.edit(view=BlackjackView())

async def setup(bot):

    await bot.add_cog(Blackjack(bot))