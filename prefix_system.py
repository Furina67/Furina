import discord
from discord.ext import commands
import json
import os

PREFIX_FILE = "prefixes.json"

class PrefixSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_prefixes(self):
        if not os.path.exists(PREFIX_FILE):
            with open(PREFIX_FILE, "w") as f:
                json.dump({}, f)
        with open(PREFIX_FILE, "r") as f:
            return json.load(f)

    def save_prefixes(self, prefixes):
        with open(PREFIX_FILE, "w") as f:
            json.dump(prefixes, f, indent=4)

    @commands.command(name="setprefix")
    @commands.has_permissions(administrator=True)
    async def setprefix(self, ctx, prefix: str):
        """Set a custom prefix for this server."""
        prefixes = self.load_prefixes()
        prefixes[str(ctx.guild.id)] = prefix
        self.save_prefixes(prefixes)

        embed = discord.Embed(
            title="<a:1000033630:1433575320782372995> Prefix Updated",
            description=f"New prefix set to `{prefix}` for **{ctx.guild.name}**.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Changed by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="removeprefix")
    @commands.has_permissions(administrator=True)
    async def removeprefix(self, ctx):
        """Remove the custom prefix (revert to default)."""
        prefixes = self.load_prefixes()
        if str(ctx.guild.id) in prefixes:
            del prefixes[str(ctx.guild.id)]
            self.save_prefixes(prefixes)
            msg = "Removed custom prefix — now using default prefix `,`."
            color = discord.Color.orange()
        else:
            msg = "<:1000033652:1433747444449017927>This server is already using the default prefix `,`."
            color = discord.Color.yellow()

        embed = discord.Embed(title="Prefix Info", description=msg, color=color)
        await ctx.send(embed=embed)

    @commands.command(name="listprefix")
    async def listprefix(self, ctx):
        """Show the current prefix(es) for this server."""
        prefixes = self.load_prefixes()
        current = prefixes.get(str(ctx.guild.id), ",")
        embed = discord.Embed(
            title="Current Prefix",
            description=f"Prefix for **{ctx.guild.name}**: `{current}`",
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PrefixSystem(bot))