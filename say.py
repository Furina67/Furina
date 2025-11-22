import discord
from discord.ext import commands

# 🔹 Add all bot owner IDs here
BOT_OWNER_IDS = [832459817485860894, 493145844166426624]

class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="say", help="Make the bot say something (Admins only or Bot Owners).")
    async def say(self, ctx, *, message: str):
        """Make the bot say a message (Admins only or Bot Owners)."""
        # Check if user is admin or one of the bot owners
        if not (ctx.author.guild_permissions.administrator or ctx.author.id in BOT_OWNER_IDS):
            embed = discord.Embed(
                title="Permission Denied",
                description="You need `administrator` permission or must be a bot owner to use this command.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Try deleting the user's command message
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        # Send the message as the bot
        await ctx.send(message)

    @say.error
    async def say_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Usage Error",
                description="Please provide a message to say.\nExample: `,say Hello World!`",
                color=discord.Color.orange()
            )
            await ctx.reply(embed=embed, mention_author=False)
        else:
            raise error


async def setup(bot):
    await bot.add_cog(Say(bot))