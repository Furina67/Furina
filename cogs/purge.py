import discord
from discord.ext import commands

class Purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = None):
        if amount is None:
            return await ctx.reply("⚠️ Specify how many messages to delete.\nExample: `,purge 10`", mention_author=False)

        if amount < 1:
            return await ctx.reply("❌ You must delete at least 1 message.", mention_author=False)

        if amount > 100:
            return await ctx.reply("❌ You can only delete up to 100 messages at once.", mention_author=False)

        deleted = await ctx.channel.purge(
            limit=amount + 1,
            check=lambda m: not m.pinned and m.id != ctx.message.id
        )

        embed = discord.Embed(
            description=f"🧹 **{len(deleted)} messages** purged by {ctx.author.mention}",
            color=discord.Color.dark_purple()
        )

        msg = await ctx.send(embed=embed)
        await msg.delete(delay=3)

    @commands.command(name="purgebot", aliases=["purgebots"])
    @commands.has_permissions(manage_messages=True)
    async def purgebot(self, ctx, amount: int = 100):
        if amount < 1:
            return await ctx.reply("❌ You must check at least 1 message.", mention_author=False)

        if amount > 1000:
            return await ctx.reply("❌ You can only scan up to 1000 messages.", mention_author=False)

        deleted = await ctx.channel.purge(
            limit=amount,
            check=lambda m: m.author.bot and not m.pinned
        )

        embed = discord.Embed(
            description=f"🤖 **{len(deleted)} bot messages** purged by {ctx.author.mention}",
            color=discord.Color.dark_purple()
        )

        msg = await ctx.send(embed=embed)
        await msg.delete(delay=3)

    @purge.error
    @purgebot.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ You don’t have permission to manage messages.", mention_author=False)
        elif isinstance(error, commands.BadArgument):
            await ctx.reply("❌ Please provide a valid number.\nExample: `,purge 10`", mention_author=False)
        else:
            raise error

async def setup(bot):
    await bot.add_cog(Purge(bot))
