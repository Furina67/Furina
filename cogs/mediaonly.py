import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import re
import time

DB = "mediaonly.db"
LINK_REGEX = re.compile(r"https?://", re.IGNORECASE)


class MediaOnly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = None
        self.active_channels = set()
        self.cooldowns = {}
        self.bypass_roles = {}
        self.warn_tracker = {}

    async def cog_load(self):
        self.db = await aiosqlite.connect(DB)

        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS media_only (
            guild_id INTEGER,
            channel_id INTEGER,
            PRIMARY KEY (guild_id, channel_id)
        )
        """)

        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS media_settings (
            guild_id INTEGER PRIMARY KEY,
            cooldown INTEGER
        )
        """)

        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS media_bypass_roles (
            guild_id INTEGER,
            role_id INTEGER,
            PRIMARY KEY (guild_id, role_id)
        )
        """)

        await self.db.commit()

        async with self.db.execute("SELECT guild_id, channel_id FROM media_only") as c:
            for g, ch in await c.fetchall():
                self.active_channels.add((g, ch))

        async with self.db.execute("SELECT guild_id, cooldown FROM media_settings") as c:
            for g, cd in await c.fetchall():
                self.cooldowns[g] = cd

        async with self.db.execute("SELECT guild_id, role_id FROM media_bypass_roles") as c:
            for g, r in await c.fetchall():
                self.bypass_roles.setdefault(g, set()).add(r)

    @app_commands.command(name="mediaonly",
                         description="Configure media-only channels and settings.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def mediaonly(self, interaction: discord.Interaction):
        view = MediaOnlyDashboard(self, interaction.guild)
        await interaction.response.send_message(view=view)
        view.message = await interaction.original_response()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return

        if (message.guild.id, message.channel.id) not in self.active_channels:
            return

        if message.author.bot:
            return

        bypass = self.bypass_roles.get(message.guild.id, set())
        if any(role.id in bypass for role in message.author.roles):
            return

        if message.attachments or LINK_REGEX.search(message.content):
            return

        try:
            await message.delete()
        except:
            return

        now = time.time()
        cooldown = self.cooldowns.get(message.guild.id, 60)
        key = (message.guild.id, message.channel.id, message.author.id)

        last = self.warn_tracker.get(key)
        if not last or now - last >= cooldown:
            self.warn_tracker[key] = now
            try:
                await message.channel.send(
                    f"{message.author.mention}, this channel is Media Only.",
                    delete_after=5
                )
            except:
                pass


class MediaOnlyDashboard(discord.ui.LayoutView):
    def __init__(self, cog, guild):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild = guild
        self.selected_channel = None
        self.message = None
        self.build()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "You do not have permission to use this panel.",
                ephemeral=True
            )
            return False
        return True

    def build(self):
        self.clear_items()

        container = discord.ui.Container()

        container.add_item(discord.ui.TextDisplay("## Media Only System"))
        container.add_item(discord.ui.Separator())

        active = [cid for gid, cid in self.cog.active_channels if gid == self.guild.id]
        if active:
            container.add_item(discord.ui.TextDisplay(
                "**Active Channels**\n" +
                "\n".join(f"â€¢ <#{cid}>" for cid in active)
            ))
        else:
            container.add_item(discord.ui.TextDisplay(
                "**Active Channels**\nNone configured."
            ))

        container.add_item(discord.ui.Separator())

        roles = self.cog.bypass_roles.get(self.guild.id, set())
        if roles:
            container.add_item(discord.ui.TextDisplay(
                "**Bypass Roles**\n" +
                "\n".join(f"â€¢ <@&{rid}>" for rid in roles)
            ))
        else:
            container.add_item(discord.ui.TextDisplay(
                "**Bypass Roles**\nNone configured."
            ))

        container.add_item(discord.ui.Separator())

        cooldown = self.cog.cooldowns.get(self.guild.id, 60)
        container.add_item(discord.ui.TextDisplay(
            f"**Warning Cooldown**\n`{cooldown} seconds`"
        ))

        # Add channel select
        select_row = discord.ui.ActionRow()
        select = discord.ui.ChannelSelect(
            placeholder="Select a text channel",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1
        )
        select.callback = self.add_channel
        select_row.add_item(select)
        container.add_item(select_row)

        # Buttons
        button_row = discord.ui.ActionRow()

        remove_channel_btn = discord.ui.Button(label="Remove Channel", style=discord.ButtonStyle.red)
        add_role_btn = discord.ui.Button(label="Add Bypass Role", style=discord.ButtonStyle.green)
        remove_role_btn = discord.ui.Button(label="Remove Bypass Role", style=discord.ButtonStyle.secondary)
        cooldown_btn = discord.ui.Button(label="Set Cooldown", style=discord.ButtonStyle.primary)

        remove_channel_btn.callback = self.remove_channel
        add_role_btn.callback = self.add_role
        remove_role_btn.callback = self.remove_role
        cooldown_btn.callback = self.set_cd

        button_row.add_item(remove_channel_btn)
        button_row.add_item(add_role_btn)
        button_row.add_item(remove_role_btn)
        button_row.add_item(cooldown_btn)

        container.add_item(button_row)

        self.add_item(container)

    async def add_channel(self, interaction: discord.Interaction):
        cid = int(interaction.data["values"][0])

        await self.cog.db.execute(
            "INSERT OR IGNORE INTO media_only VALUES (?, ?)",
            (self.guild.id, cid)
        )
        await self.cog.db.commit()

        self.cog.active_channels.add((self.guild.id, cid))

        self.build()
        await interaction.response.edit_message(view=self)

    async def remove_channel(self, interaction: discord.Interaction):
        active = [
            cid for gid, cid in self.cog.active_channels
            if gid == self.guild.id
        ]

        if not active:
            return await interaction.response.send_message(
                "No active channels.",
                ephemeral=True
            )

        view = RemoveChannelView(self.cog, self.guild, self, active)
        await interaction.response.send_message(view=view, ephemeral=True)

    async def add_role(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            view=RoleSelectView(self.cog, self.guild, self, "add"),
            ephemeral=True
        )

    async def remove_role(self, interaction: discord.Interaction):
        roles = list(self.cog.bypass_roles.get(self.guild.id, set()))

        if not roles:
            return await interaction.response.send_message(
                "No bypass roles configured.",
                ephemeral=True
            )

        view = RemoveRoleView(self.cog, self.guild, self, roles)
        await interaction.response.send_message(view=view, ephemeral=True)

    async def set_cd(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            SetCooldownModal(self.cog, self.guild.id, self)
        )


class RemoveChannelView(discord.ui.View):
    def __init__(self, cog, guild, parent, channels):
        super().__init__(timeout=60)
        self.cog = cog
        self.guild = guild
        self.parent = parent

        options = [
            discord.SelectOption(
                label=guild.get_channel(cid).name,
                value=str(cid)
            )
            for cid in channels
            if guild.get_channel(cid)
        ]

        select = discord.ui.Select(
            placeholder="Select channel to remove",
            options=options
        )
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):
        cid = int(interaction.data["values"][0])

        await self.cog.db.execute(
            "DELETE FROM media_only WHERE guild_id=? AND channel_id=?",
            (self.guild.id, cid)
        )
        await self.cog.db.commit()

        self.cog.active_channels.discard((self.guild.id, cid))

        self.parent.build()
        await self.parent.message.edit(view=self.parent)
        await interaction.response.send_message("Channel removed.", ephemeral=True)


class RemoveRoleView(discord.ui.View):
    def __init__(self, cog, guild, parent, roles):
        super().__init__(timeout=60)
        self.cog = cog
        self.guild = guild
        self.parent = parent

        options = [
            discord.SelectOption(
                label=guild.get_role(rid).name,
                value=str(rid)
            )
            for rid in roles
            if guild.get_role(rid)
        ]

        select = discord.ui.Select(
            placeholder="Select role to remove",
            options=options
        )
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):
        rid = int(interaction.data["values"][0])

        await self.cog.db.execute(
            "DELETE FROM media_bypass_roles WHERE guild_id=? AND role_id=?",
            (self.guild.id, rid)
        )
        await self.cog.db.commit()

        self.cog.bypass_roles.get(self.guild.id, set()).discard(rid)

        self.parent.build()
        await self.parent.message.edit(view=self.parent)
        await interaction.response.send_message("Role removed.", ephemeral=True)


class RoleSelectView(discord.ui.View):
    def __init__(self, cog, guild, parent, mode):
        super().__init__(timeout=60)
        self.cog = cog
        self.guild = guild
        self.parent = parent
        self.mode = mode

        select = discord.ui.RoleSelect(min_values=1, max_values=10)
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        role_ids = [int(r) for r in interaction.data["values"]]

        for rid in role_ids:
            if self.mode == "add":
                await self.cog.db.execute(
                    "INSERT OR IGNORE INTO media_bypass_roles VALUES (?, ?)",
                    (self.guild.id, rid)
                )
                self.cog.bypass_roles.setdefault(self.guild.id, set()).add(rid)

        await self.cog.db.commit()

        self.parent.build()
        await self.parent.message.edit(view=self.parent)
        await interaction.delete_original_response()


class SetCooldownModal(discord.ui.Modal, title="Set Warning Cooldown"):
    value = discord.ui.TextInput(label="Cooldown (seconds)")

    def __init__(self, cog, guild_id, parent):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id
        self.parent = parent

    async def on_submit(self, interaction: discord.Interaction):
        try:
            seconds = max(5, int(self.value.value.strip()))
        except:
            return await interaction.response.send_message("Invalid number.", ephemeral=True)

        await self.cog.db.execute(
            "INSERT OR REPLACE INTO media_settings VALUES (?, ?)",
            (self.guild_id, seconds)
        )
        await self.cog.db.commit()

        self.cog.cooldowns[self.guild_id] = seconds

        self.parent.build()
        await interaction.response.edit_message(view=self.parent)


async def setup(bot):
    await bot.add_cog(MediaOnly(bot))