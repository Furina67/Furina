import discord
from discord.ext import commands

class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="say")
    @commands.has_permissions(administrator=True)
    async def say(self, ctx, *, message: str):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        await ctx.send(message)

    @say.error
    async def say_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply(
                "❌ You need **Administrator** permission to use this command.",
                mention_author=False
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(
                "❌ Please provide a message.\nExample: `,say Hello world!`",
                mention_author=False
            )
        else:
            raise error

async def setup(bot):
    await bot.add_cog(Say(bot))
