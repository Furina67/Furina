import discord
from discord.ext import commands
import asyncio  # needed for the delay

class TicketEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Replace with the ID of your ticket category
    TICKET_CATEGORY_ID = 1399197959530352753

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if isinstance(channel, discord.TextChannel) and channel.category_id == self.TICKET_CATEGORY_ID:
            await asyncio.sleep(2)  # wait 2 seconds before sending
            embed = discord.Embed(
                title="Staff Application",
                description=(
                    "-# Answer all questions truthfully, use complete sentences, and take this seriously!\n"
                    "・What are your pronouns & age?\n"
                    "・What's your timezone?\n"
                    "・Which languages can you speak?\n"
                    "・Tell us a bit about you!\n\n"
                    "・List some basic mod commands (e.g., managing roles, bots, permissions)\n"
                    "・If you have previous experience, what server(s) did you staff in? Yes / No\n"
                    "-# If Yes, please provide server names and your role(s):\n"
                    "・Why do you want to become a moderator for our Discord server?\n"
                    "・Why do you think we'll choose you over other applicants?\n\n"
                    "・How would you handle a conflict between two users?\n"
                    "・How would you handle a disrespectful member?\n"
                    "・How many hours can you dedicate to moderating per week?\n"
                    "・What times of day are you most active on Discord?\n\n"
                    "・Is there anything else you'd like us to know about you or your experience?\n"
                    "・Are you familiar with the rules and guidelines of our server? Yes / No"
                ),
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(TicketEmbed(bot))