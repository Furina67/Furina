import discord
from discord.ext import commands
import aiohttp

class Define(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="define")
    async def define(self, ctx, *, word: str = None):
        if not word:
            return await ctx.reply("Please provide a word to define.\nExample: `.define chemistry`", mention_author=False)

        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return await ctx.reply(f"No definition found for `{word}`.", mention_author=False)
                data = await response.json()

        try:
            meaning_data = data[0]["meanings"][0]
            definition = meaning_data["definitions"][0].get("definition", "No definition available.")
            example = meaning_data["definitions"][0].get("example", "No example available.")
            part_of_speech = meaning_data.get("partOfSpeech", "N/A")

            embed = discord.Embed(
                title=f"Definition of `{word}`",
                color=discord.Color.blue()
            )
            embed.add_field(name="Part of Speech", value=part_of_speech, inline=False)
            embed.add_field(name="Definition", value=definition, inline=False)
            embed.add_field(name="Example", value=example, inline=False)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

            await ctx.reply(embed=embed, mention_author=False)

        except Exception:
            await ctx.reply(f"Error processing definition for `{word}`.", mention_author=False)

async def setup(bot):
    await bot.add_cog(Define(bot))
