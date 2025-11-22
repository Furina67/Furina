# cogs/leave_server.py
import discord
from discord.ext import commands

class LeaveServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # List of allowed users
        self.allowed_ids = [832459817485860894, 1356075369853223033]

    @commands.command(name="leave")
    async def leave(self, ctx, guild_id: int = None):
        """Makes the bot leave a server. Can specify guild ID or leave current server."""
        # Check if user is allowed
        if ctx.author.id not in self.allowed_ids:
            await ctx.send("You are not allowed to use this command.")
            return

        if guild_id:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await ctx.send("I am not in a server with that ID.")
                return
        else:
            # If no guild_id is given, leave the current server
            guild = ctx.guild

        await guild.leave()
        await ctx.send(f"Left the server: {guild.name}")

# Cog setup
async def setup(bot):
    await bot.add_cog(LeaveServer(bot))