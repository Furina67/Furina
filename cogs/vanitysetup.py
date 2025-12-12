import discord
from discord.ext import commands
import json
import os
import asyncio
from typing import Optional, Union

DATA_FILE = "vanity_data.json"
SAVE_LOCK = asyncio.Lock()
PROMPT_TIMEOUT = 60


def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


async def save_data(data):
    async with SAVE_LOCK:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


_vanity_data = load_data()


def get_user_status(member: discord.Member) -> Optional[str]:
    for act in member.activities or []:
        if isinstance(act, discord.CustomActivity) and getattr(act, "name", None):
            return act.name
    return None


def replace_placeholders(text: str, member: discord.Member, cfg: dict) -> str:
    server = member.guild.name if member.guild else ""
    server_id = member.guild.id if member.guild else ""
    role = member.guild.get_role(cfg.get("role_id")) if cfg.get("role_id") and member.guild else None
    channel = member.guild.get_channel(cfg.get("channel_id")) if cfg.get("channel_id") and member.guild else None

    return (
        text.replace("{user}", member.mention)
        .replace("{username}", member.name)
        .replace("{discriminator}", member.discriminator)
        .replace("{id}", str(member.id))
        .replace("{avatar}", str(member.display_avatar.url))
        .replace("{server}", server)
        .replace("{guild}", server)
        .replace("{server_id}", str(server_id))
        .replace("{member_count}", str(member.guild.member_count if member.guild else ""))
        .replace("{role}", role.mention if role else "")
        .replace("{role_name}", role.name if role else "")
        .replace("{channel}", channel.mention if channel else "")
        .replace("{channel_name}", channel.name if channel else "")
        .replace("{word}", cfg.get("word", ""))
        .replace("{status}", get_user_status(member) or "")
    )


class Step1Modal(discord.ui.Modal, title="Vanity Setup — Step 1"):
    vanity_word = discord.ui.TextInput(label="Vanity Word", required=True, max_length=200)
    role_input = discord.ui.TextInput(label="Role (mention or ID)", required=True, max_length=100)
    channel_input = discord.ui.TextInput(label="Channel (mention or ID)", required=True, max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("This must be used inside a server.", ephemeral=True)

        cog = interaction.client.get_cog("Vanity")
        gid = str(interaction.guild.id)

        role = None
        role_txt = self.role_input.value.strip()
        if role_txt.isdigit():
            role = interaction.guild.get_role(int(role_txt))
        elif role_txt.startswith("<@&"):
            role = interaction.guild.get_role(int(role_txt[3:-1]))
        else:
            role = discord.utils.get(interaction.guild.roles, name=role_txt)

        if not role:
            return await interaction.response.send_message("Role not found.", ephemeral=True)

        channel = None
        ch_txt = self.channel_input.value.strip()
        if ch_txt.isdigit():
            channel = interaction.guild.get_channel(int(ch_txt))
        elif ch_txt.startswith("<#"):
            channel = interaction.guild.get_channel(int(ch_txt[2:-1]))
        else:
            channel = discord.utils.get(interaction.guild.text_channels, name=ch_txt.lstrip("#"))

        if not channel or not channel.permissions_for(interaction.guild.me).send_messages:
            return await interaction.response.send_message("Invalid or inaccessible channel.", ephemeral=True)

        cfg = cog.vanity_data.setdefault(gid, {})
        cfg["word"] = self.vanity_word.value.strip()
        cfg["role_id"] = role.id
        cfg["channel_id"] = channel.id
        await cog._save()

        await interaction.response.send_message(
            "Basic settings saved. Choose message mode:",
            ephemeral=True,
            view=ModeSelectView(interaction.user.id)
        )


class TextModal(discord.ui.Modal, title="Vanity Text Message"):
    message_text = discord.ui.TextInput(style=discord.TextStyle.long, required=True, max_length=1800)

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Vanity")
        cfg = cog.vanity_data.setdefault(str(interaction.guild.id), {})
        cfg["embed_enabled"] = False
        cfg["message_text"] = self.message_text.value
        await cog._save()

        preview = replace_placeholders(self.message_text.value, interaction.user, cfg)
        await interaction.response.send_message(f"Saved.\nPreview:\n{preview}", ephemeral=True)


class EmbedModal(discord.ui.Modal, title="Vanity Embed"):
    title_text = discord.ui.TextInput(required=False)
    description = discord.ui.TextInput(style=discord.TextStyle.long, required=False)
    image = discord.ui.TextInput(required=False)
    thumbnail = discord.ui.TextInput(required=False)
    footer = discord.ui.TextInput(required=False)

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Vanity")
        cfg = cog.vanity_data.setdefault(str(interaction.guild.id), {})

        def v(x):
            return x.strip() if x and x.strip().lower() != "skip" else None

        cfg["embed_enabled"] = True
        cfg["embed_title"] = v(self.title_text.value)
        cfg["embed_description"] = v(self.description.value)
        cfg["embed_image"] = v(self.image.value)
        cfg["embed_thumbnail"] = v(self.thumbnail.value)
        cfg["embed_footer"] = v(self.footer.value)

        await cog._save()
        preview = cog.create_vanity_message(cfg, interaction.user)
        await interaction.response.send_message("Saved. Preview:", embed=preview, ephemeral=True)


class ModeSelectView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not allowed.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Text Mode", style=discord.ButtonStyle.primary)
    async def text(self, interaction, _):
        await interaction.response.send_modal(TextModal())

    @discord.ui.button(label="Embed Mode", style=discord.ButtonStyle.primary)
    async def embed(self, interaction, _):
        await interaction.response.send_modal(EmbedModal())


class Vanity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vanity_data = _vanity_data

    async def _save(self):
        await save_data(self.vanity_data)

    def create_vanity_message(self, cfg, member):
        if not cfg.get("embed_enabled"):
            return replace_placeholders(cfg.get("message_text", ""), member, cfg)

        def p(v): return replace_placeholders(v or "", member, cfg)

        embed = discord.Embed(
            title=p(cfg.get("embed_title")),
            description=p(cfg.get("embed_description")),
            color=discord.Color.blurple()
        )

        if cfg.get("embed_thumbnail"):
            embed.set_thumbnail(url=p(cfg["embed_thumbnail"]))
        if cfg.get("embed_image"):
            embed.set_image(url=p(cfg["embed_image"]))
        if cfg.get("embed_footer"):
            embed.set_footer(text=p(cfg["embed_footer"]))

        return embed

    @commands.command(name="vanitysetup")
    @commands.has_permissions(manage_guild=True)
    async def vanitysetup(self, ctx):
        embed = discord.Embed(
            title="Vanity Setup Panel",
            description="Use the buttons below to configure the system.",
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed, view=VanitySetupView(ctx.author))


async def setup(bot):
    await bot.add_cog(Vanity(bot))
