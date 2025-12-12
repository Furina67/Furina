import discord
from discord.ext import commands
from discord import app_commands, ui
import json
import os
from datetime import datetime

CONFIG_PATH = "welcome_config.json"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            json.dump({}, f)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)

config = load_config()

def ordinal(n: int):
    if 10 <= (n % 100) <= 20:
        return f"{n}th"
    return f"{n}{ {1:'st',2:'nd',3:'rd'}.get(n % 10, 'th') }"

def fmt_dt(dt: datetime):
    return dt.strftime("%d %B %Y • %H:%M") if dt else ""

def boost_tier_text(count: int):
    return "None (Level 0)" if count <= 0 else f"Tier {count} (Level {count})"

def replace_vars(text: str, member: discord.Member):
    if not text:
        return ""

    g = member.guild
    mapping = {
        "{user_name}": member.name,
        "{user_tag}": str(member),
        "{user_mention}": member.mention,
        "{user_avatar}": member.display_avatar.url,
        "{user_displayname}": member.display_name,
        "{user_discriminator}": member.discriminator,
        "{user_id}": str(member.id),
        "{user_createdate}": fmt_dt(member.created_at),
        "{user_joined_timestamp}": fmt_dt(member.joined_at or datetime.utcnow()),
        "{server_name}": g.name,
        "{server_icon}": g.icon.url if g.icon else "",
        "{server_createdate}": fmt_dt(g.created_at),
        "{server_created_timestamp}": fmt_dt(g.created_at),
        "{server_owner}": g.owner.name if g.owner else "",
        "{server_owner_mention}": g.owner.mention if g.owner else "",
        "{server_membercount}": str(g.member_count),
        "{server_membercount_ordinal}": ordinal(g.member_count),
        "{server_boosts}": str(g.premium_subscription_count),
        "{server_boost_tier}": boost_tier_text(g.premium_subscription_count),
        "{server_region}": str(getattr(g, "region", "Unknown")),
        "{server_roles}": str(len(g.roles) - 1),
        "{server_channels}": str(len(g.channels)),
        "{server_text_channels}": str(len([c for c in g.channels if isinstance(c, discord.TextChannel)])),
        "{server_voice_channels}": str(len([c for c in g.channels if isinstance(c, discord.VoiceChannel)])),
    }

    for k, v in mapping.items():
        text = text.replace(k, v)

    return text

class SingleLineModal(ui.Modal):
    def __init__(self, title, key, data, placeholder=""):
        super().__init__(title=title)
        self.key = key
        self.data = data
        self.input = ui.TextInput(label=title, placeholder=placeholder)
        self.add_item(self.input)

    async def on_submit(self, interaction):
        self.data[self.key] = self.input.value
        await interaction.response.send_message("Updated.", ephemeral=True)

class MultiLineModal(ui.Modal):
    def __init__(self, title, key, data, placeholder):
        super().__init__(title=title)
        self.key = key
        self.data = data
        self.input = ui.TextInput(label=title, placeholder=placeholder, style=discord.TextStyle.long)
        self.add_item(self.input)

    async def on_submit(self, interaction):
        self.data[self.key] = self.input.value
        await interaction.response.send_message("Updated.", ephemeral=True)

class ColorModal(ui.Modal):
    def __init__(self, data):
        super().__init__(title="Set Colour")
        self.data = data
        self.input = ui.TextInput(label="HEX Colour", placeholder="#5865F2")
        self.add_item(self.input)

    async def on_submit(self, interaction):
        try:
            self.data["color"] = int(self.input.value.lstrip("#"), 16)
            await interaction.response.send_message("Updated.", ephemeral=True)
        except:
            await interaction.response.send_message("Invalid value.", ephemeral=True)

class WelcomeSetupView(ui.View):
    def __init__(self, interaction, data, guild_id):
        super().__init__(timeout=None)
        self.owner = interaction.user.id
        self.data = data
        self.guild_id = guild_id
        self.msg = interaction

    def check(self, interaction):
        return interaction.user.id == self.owner

    async def deny(self, interaction):
        await interaction.response.send_message("Not allowed.", ephemeral=True)

    @ui.button(label="Set Title")
    async def title(self, interaction, _):
        if not self.check(interaction): return await self.deny(interaction)
        await interaction.response.send_modal(MultiLineModal("Title", "title", self.data, ""))

    @ui.button(label="Set Description")
    async def desc(self, interaction, _):
        if not self.check(interaction): return await self.deny(interaction)
        await interaction.response.send_modal(MultiLineModal("Description", "description", self.data, ""))

    @ui.button(label="Set Colour")
    async def colour(self, interaction, _):
        if not self.check(interaction): return await self.deny(interaction)
        await interaction.response.send_modal(ColorModal(self.data))

    @ui.button(label="Preview")
    async def preview(self, interaction, _):
        if not self.check(interaction): return await self.deny(interaction)
        fake = interaction.user
        embed = discord.Embed(
            title=replace_vars(self.data.get("title", ""), fake),
            description=replace_vars(self.data.get("description", ""), fake),
            color=self.data.get("color", 0x5865F2)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="Finish")
    async def finish(self, interaction, _):
        if not self.check(interaction): return await self.deny(interaction)
        await interaction.response.send_message("Mention a channel.", ephemeral=True)

        def check(m):
            return m.author.id == interaction.user.id and m.channel == interaction.channel

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=60)
        except:
            return

        if not msg.channel_mentions:
            return

        ch = msg.channel_mentions[0]
        self.data["channel"] = ch.id
        config[self.guild_id] = self.data
        save_config(config)
        await interaction.followup.send("Saved.", ephemeral=True)
        await self.msg.edit_original_response(view=None)
        self.stop()

class WelcomeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="welcome_setup")
    async def welcome_setup(self, interaction):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("No permission.", ephemeral=True)

        gid = str(interaction.guild.id)
        data = config.get(gid, {
            "title": "Welcome to {server_name}",
            "description": "Hello {user_name}",
            "color": 0x5865F2,
            "ping": False,
            "channel": None
        })

        embed = discord.Embed(title="Welcome Setup")
        view = WelcomeSetupView(interaction, data, gid)
        await interaction.response.send_message(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        data = config.get(str(member.guild.id))
        if not data:
            return

        embed = discord.Embed(
            title=replace_vars(data.get("title", ""), member),
            description=replace_vars(data.get("description", ""), member),
            color=data.get("color", 0x5865F2)
        )

        ch = member.guild.get_channel(data.get("channel"))
        if ch:
            await ch.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WelcomeCommands(bot))
