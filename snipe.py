import discord
from discord.ext import commands
from collections import deque
import json
from datetime import datetime

SNIPE_FILE = "snipe.json"
SETTINGS_FILE = "snipe_settings.json"

class Snipe(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Load snipes
        try:
            with open(SNIPE_FILE, "r") as f:
                data = json.load(f)
                self.snipes = {int(k): deque(v, maxlen=10) for k, v in data.items()}
        except:
            self.snipes = {}

        # Load settings
        try:
            with open(SETTINGS_FILE, "r") as f:
                self.settings = json.load(f)
        except:
            self.settings = {}

    def save_snipes(self):
        with open(SNIPE_FILE, "w") as f:
            json.dump({str(k): list(v) for k, v in self.snipes.items()}, f, indent=4)

    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        messages = self.snipes.setdefault(message.channel.id, deque(maxlen=10))
        messages.appendleft({
            "author_id": message.author.id,
            "author_name": message.author.name,
            "content": message.content,
            "attachments": [a.url for a in message.attachments],
            "time": datetime.utcnow().isoformat()
        })
        self.save_snipes()

    def has_snipe_permission(self, ctx):
        role_id = self.settings.get(str(ctx.guild.id))
        if not role_id:
            return True
        role = ctx.guild.get_role(role_id)
        return role in ctx.author.roles if role else True

    # --- .snipe command ---
    @commands.command(name="snipe")
    async def snipe(self, ctx, arg: str = None):
        """Snipe deleted messages. Use '.snipe all' to snipe all messages."""
        if not self.has_snipe_permission(ctx):
            return await ctx.send("❌ You don't have permission to use this command.")

        messages = self.snipes.get(ctx.channel.id)
        if not messages:
            return await ctx.send("Nothing to snipe!")

        if arg and arg.lower() == "all":
            embed = discord.Embed(
                title=f"Deleted Messages in #{ctx.channel.name}",
                color=discord.Color.blue()
            )
            for idx, msg in enumerate(messages, start=1):
                author = ctx.guild.get_member(msg["author_id"])
                name = author.display_name if author else msg["author_name"]

                content = msg["content"] if msg["content"] else "[Attachment Only]"
                utc_time = datetime.fromisoformat(msg["time"])
                timestamp = int(utc_time.timestamp())
                field_value = content
                if msg["attachments"]:
                    attachments_text = "\n".join(msg["attachments"][1:]) if len(msg["attachments"]) > 1 else ""
                    if attachments_text:
                        field_value += f"\n{attachments_text}"

                embed.add_field(
                    name=f"{idx}. {name} • <t:{timestamp}:f>",
                    value=field_value,
                    inline=False
                )

                if msg["attachments"]:
                    embed.set_image(url=msg["attachments"][0])

            await ctx.send(embed=embed)
        else:
            await self.send_snipe_embed(ctx, messages[0])

    async def send_snipe_embed(self, ctx, msg):
        user = ctx.guild.get_member(msg["author_id"])
        embed = discord.Embed(
            description=msg["content"] if msg["content"] else "[Attachment Only]",
            color=discord.Color.blue()
        )

        if user:
            embed.set_author(
                name=user.display_name,
                icon_url=user.display_avatar.url
            )
        else:
            embed.set_author(name=msg["author_name"])

        utc_time = datetime.fromisoformat(msg["time"])
        timestamp = int(utc_time.timestamp())
        embed.set_footer(text=f"Deleted at <t:{timestamp}:f>")

        if msg["attachments"]:
            embed.set_image(url=msg["attachments"][0])
            if len(msg["attachments"]) > 1:
                for i, att in enumerate(msg["attachments"][1:], start=2):
                    embed.add_field(name=f"Attachment {i}", value=att, inline=False)

        await ctx.send(embed=embed)

    # --- .snipesettings command ---
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def snipesettings(self, ctx, *, role_input: str = None):
        """
        Set a role that can use snipe commands.
        Usage: .snipesettings @Role or .snipesettings RoleName or .snipesettings 123456789
        To remove restriction: .snipesettings clear
        """
        if role_input is None:
            current_role_id = self.settings.get(str(ctx.guild.id))
            if current_role_id:
                role = ctx.guild.get_role(current_role_id)
                role_name = role.name if role else "Unknown Role"
                await ctx.send(
                    f"ℹ️ Current snipe role: **{role_name}** (ID: {current_role_id})\n"
                    f"To change it, use `.snipesettings <role>`\n"
                    f"To remove the restriction, use `.snipesettings clear`"
                )
            else:
                await ctx.send(
                    f"ℹ️ No snipe role is set. Everyone can use snipe commands.\n"
                    f"To restrict access, use `.snipesettings <role>`"
                )
            return

        if role_input.lower() in ["clear", "reset"]:
            if str(ctx.guild.id) in self.settings:
                del self.settings[str(ctx.guild.id)]
                self.save_settings()
                await ctx.send(
                    "✅ Snipe role restriction removed. Everyone can now use snipe commands.\n"
                    f"To set a new role, use `.snipesettings <role>`"
                )
            else:
                await ctx.send(
                    "ℹ️ No snipe role was set.\nUse `.snipesettings <role>` to restrict access."
                )
            return

        role = None
        if ctx.message.role_mentions:
            role = ctx.message.role_mentions[0]
        elif role_input.isdigit():
            role = ctx.guild.get_role(int(role_input))
        else:
            for r in ctx.guild.roles:
                if r.name.lower() == role_input.lower():
                    role = r
                    break

        if not role:
            await ctx.send(
                f"❌ Role not found: **{role_input}**\n"
                f"Try mentioning the role (@Role), using the role ID, or the exact role name."
            )
            return

        self.settings[str(ctx.guild.id)] = role.id
        self.save_settings()
        await ctx.send(
            f"✅ Snipe permission set to role: **{role.name}**\n"
            f"Only members with this role can now use snipe commands.\n"
            f"To remove restriction, use `.snipesettings clear`"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Snipe(bot))