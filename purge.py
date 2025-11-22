import discord

from discord.ext import commands

class Purge(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    # ========================

    # Normal purge command

    # ========================

    @commands.command(name="purge", aliases=["clear"])

    @commands.has_permissions(manage_messages=True)

    async def purge(self, ctx, amount: int = None):

        """Delete a specific number of recent messages."""

        if amount is None:

            return await ctx.reply("⚠️ Please specify how many messages to delete.\nExample: `,purge 10`")

        if amount < 1:

            return await ctx.reply("❌ You must delete at least 1 message.")

        if amount > 100:

            return await ctx.reply("⚠️ You can only delete up to 100 messages at once.")

        deleted = await ctx.channel.purge(limit=amount + 1)

        embed = discord.Embed(

            description=f"🧹 **{len(deleted) - 1} messages** have been purged by {ctx.author.mention}",

            color=discord.Color.dark_purple()

        )

        msg = await ctx.send(embed=embed)

        await msg.delete(delay=3)

    # ========================

    # Purge bot messages only

    # ========================

    @commands.command(name="purgebot", aliases=["purgebots"])

    @commands.has_permissions(manage_messages=True)

    async def purgebot(self, ctx, amount: int = 100):

        """Delete only bot messages from the last N messages."""

        if amount < 1:

            return await ctx.reply("❌ You must check at least 1 message.")

        if amount > 1000:

            return await ctx.reply("⚠️ You can only check up to 1000 recent messages.")

        deleted = await ctx.channel.purge(

            limit=amount,

            check=lambda m: m.author.bot

        )

        embed = discord.Embed(

            description=f"🤖 **{len(deleted)} bot messages** have been purged by {ctx.author.mention}",

            color=discord.Color.dark_purple()

        )

        msg = await ctx.send(embed=embed)

        await msg.delete(delay=3)

    # ========================

    # Error handling

    # ========================

    @purge.error

    @purgebot.error

    async def purge_error(self, ctx, error):

        if isinstance(error, commands.MissingPermissions):

            await ctx.reply("🚫 You don't have permission to manage messages.")

        elif isinstance(error, commands.BadArgument):

            await ctx.reply("⚠️ Please use a valid number, e.g. `,purge 10`.")

        else:

            raise error

async def setup(bot):
    await bot.add_cog(Purge(bot))