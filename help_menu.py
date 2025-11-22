import discord
from discord.ext import commands

# Dictionary storing all commands per category
COMMANDS = {
    "General / Info": {
        "av/avatar": "Shows a user’s avatar",
        "help": "Displays all available commands",
        "membercount/mc": "Shows total members in the server",
        "ping": "Checks bot latency",
        "serverinfo/si": "Displays server information",
        "accage": "Displays the user's account age",
        "afk": "Set AFK status"
    },
    "Fun": {
        "blackjack": "Play a game of blackjack",
        "coinflip": "Flips a coin",
        "husbando": "Shows a random husbando",
        "setmeme": "Automatically posts memes within 5-10 minutes (admin only)",
        "mines": "Play a minesweeper-style game",
        "nitro": "Pranks users with a fake Nitro link",
        "waifu": "Shows a random waifu",
        "ttt": "Play Tictactoe with a user",
        "ship": "Ships two users together"
    },
    "Moderation": {
        "kick": "Kick a member",
        "ban": "Ban a member",
        "unban": "Unban a member",
        "to": "Timeout a member",
        "rto": "Remove timeout",
        "purge": "Delete multiple messages",
        "resetnick": "Reset nickname",
        "setnick": "Set nickname",
        "nuke": "Delete and recreate channel",
        "say": "Bot sends a custom message"
    },
    "Utility": {
        "embed": "Create a custom embed message",
        "snipe": "Retrieve the most recently deleted message in the channel",
        "snipeall": "Retrieve all recently deleted messages in the channel",
        "remind": "Set a reminder for yourself and get notified later",
        "userinfo": "View detailed information about a user",
        "roleinfo": "Get information about a specific role",
        "botinfo": "Display info and stats about the bot",
        "invite": "Get the bot’s invite link to add it to your server",
        "calc": "Perform quick math calculations",
        "define": "Get definitions and meanings of words",
        "checkvanity": "Check if a custom Discord invite link (vanity URL) is available or taken",
        "counting {channel}": "Sets a counting channel"
    },
    "Giveaway": {
        "gstart {duration} {winners} {prize}": "Start a giveaway",
        "greroll": "Reroll the giveaway",
        "gend": "End the giveaway",
        "/claimtime": "Displays the claim time of a user",
        "/claimtime_add": "Add a claim time for a role",
        "/claimtime_remove": "Remove a claim time for a role",
        "/claimtime_display": "Display claim time info for roles",
        "giveaway_log {channel}": "Set the giveaway log channel",
        "setmanager {role}": "Set the giveaway manager role",
        "giveaway_config": "Configure giveaway settings"
    },
    "Status Role": {
        "setvanity": "Set the server’s vanity keyword and role. Members including that word in their Discord status will automatically receive the assigned role (admin only; only one vanity setup per server at a time)",
        "removevanity": "Remove the current vanity keyword and role setup. Members will no longer automatically receive or lose roles based on their status keyword until a new vanity is set",
        "vanityinfo": "View the server’s current vanity role setup. Shows the active vanity keyword and the role linked to it"
    }
}

# Emoji dictionary for categories
CATEGORY_EMOJIS = {
    "General / Info": "<:1000033658:1433766326543057048>",
    "Fun": "<a:1000033695:1433928688914792448>",
    "Moderation": "<:1000033759:1434607022590001193>",
    "Utility": "<:1000033760:1434607259635155004>",
    "Giveaway": "<a:1000033761:1434607650942877778>",
    "Status Role": "<:1000033762:1434608514755723331>"
}

class HelpDropdown(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label=category, description=f"{category} commands")
            for category in COMMANDS.keys()
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot use this menu!", ephemeral=True)
            return

        category = self.values[0]
        embed = discord.Embed(title=f"{category} Commands", color=discord.Color.blue())

        description = ""
        for cmd, desc in COMMANDS[category].items():
            description += f"<:1000033547:1433343890831966208>**{cmd}**\n<a:1000033534:1433228352512065606> {desc}\n\n"

        embed.description = description.strip()
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(HelpDropdown(author))

class HelpMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")

    @commands.command(name="help")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="Help Menu",
            description=f"""
Welcome to Furina

{CATEGORY_EMOJIS['General / Info']} General / Info Commands
{CATEGORY_EMOJIS['Moderation']} Moderation Commands
{CATEGORY_EMOJIS['Fun']} Fun Commands
{CATEGORY_EMOJIS['Utility']} Utility Commands
{CATEGORY_EMOJIS['Giveaway']} Giveaway Commands
{CATEGORY_EMOJIS['Status Role']} Status Role Commands
""",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=HelpView(ctx.author))

async def setup(bot):
    await bot.add_cog(HelpMenu(bot))