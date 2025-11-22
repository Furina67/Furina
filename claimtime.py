import discord
from discord.ext import commands
from discord import app_commands
import json, os
from typing import Optional

CLAIMTIME_FILE = "claimtime_config.json"

def load_claimtime_data() -> dict:
    if os.path.exists(CLAIMTIME_FILE):
        try:
            with open(CLAIMTIME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[claimtime] Failed to load JSON: {e}")
    return {}

def save_claimtime_data(data: dict):
    try:
        with open(CLAIMTIME_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[claimtime] Failed to save JSON: {e}")

def build_blue_embed(title: str, desc: str):
    return discord.Embed(title=title, description=desc, color=discord.Color.blurple())

claimtime_config = load_claimtime_data()

# ----------------------------------------------------------
class Claimtime(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("[claimtime] Cog loaded")

    # Helper: return total claimtime for a user
    async def get_total_claimtime_for_user(self, member: discord.Member) -> int:
        total = 0
        gid = str(member.guild.id)
        cfg = claimtime_config.get(gid, {})
        role_map = cfg.get("role_claimtimes", {})
        for rid, data in role_map.items():
            role = member.guild.get_role(int(rid))
            if role and role in member.roles:
                if isinstance(data, dict):
                    total += int(data.get("seconds", 0))
                else:
                    total += int(data)  # fallback for old entries
        return total

    # ------------------------------------------------------
    @app_commands.command(name="claimtime_add", description="Set claimtime for a role")
    @app_commands.describe(
        role="Role to set claimtime for",
        duration="Claimtime duration (e.g. 10s, 5m, 1h)",
        override="Whether to override existing claimtime for this role"
    )
    async def slash_claimtime_add(
        self, 
        interaction: discord.Interaction, 
        role: discord.Role, 
        duration: str, 
        override: Optional[bool] = False
    ):
        try:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Only admins can use this command.", ephemeral=True)
                return

            # convert to seconds
            seconds = self.parse_time(duration)

            gid = str(interaction.guild.id)
            cfg = claimtime_config.setdefault(gid, {}).setdefault("role_claimtimes", {})

            # handle old entries
            existing = cfg.get(str(role.id))
            if isinstance(existing, int):
                existing = {"seconds": existing, "override": False}
                cfg[str(role.id)] = existing

            if existing and not override:
                await interaction.response.send_message(
                    f"⚠️ {role.mention} already has a claimtime of `{existing.get('seconds', 0)}` seconds. "
                    "Use the `override` option to replace it.",
                    ephemeral=True
                )
                return

            cfg[str(role.id)] = {"seconds": seconds, "override": override}
            save_claimtime_data(claimtime_config)

            label = " (Override)" if override else ""
            await interaction.response.send_message(
                embed=build_blue_embed("Claimtime Added",
                                       f"Role {role.mention} now has `{seconds}` seconds claimtime{label}."),
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)

    # ------------------------------------------------------
    @app_commands.command(name="claimtime_remove", description="Remove claimtime from a role")
    @app_commands.describe(role="Role to remove claimtime from")
    async def slash_claimtime_remove(self, interaction: discord.Interaction, role: discord.Role):
        try:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Only admins can use this command.", ephemeral=True)
                return

            gid = str(interaction.guild.id)
            cfg = claimtime_config.get(gid, {}).get("role_claimtimes", {})
            if str(role.id) in cfg:
                del claimtime_config[gid]["role_claimtimes"][str(role.id)]
                save_claimtime_data(claimtime_config)
                await interaction.response.send_message(embed=build_blue_embed("Removed", f"Removed claimtime from {role.mention}"), ephemeral=True)
            else:
                await interaction.response.send_message(embed=build_blue_embed("Not Found", f"{role.mention} has no claimtime set."), ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)

    # ------------------------------------------------------
    @app_commands.command(name="claimtime", description="View total claimtime for yourself or another user")
    @app_commands.describe(user="Optional user to check")
    async def slash_claimtime(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        try:
            member = user or interaction.user
            total = await self.get_total_claimtime_for_user(member)
            gid = str(member.guild.id)
            cfg = claimtime_config.get(gid, {}).get("role_claimtimes", {})

            lines = []
            for rid, data in cfg.items():
                role = member.guild.get_role(int(rid))
                if role and role in member.roles:
                    if isinstance(data, dict):
                        label = " (Override)" if data.get("override") else ""
                        seconds = data.get("seconds", 0)
                    else:
                        label = ""
                        seconds = data
                    lines.append(f"{role.mention}: `{seconds}s`{label}")

            embed_desc = "\n".join(lines)
            embed_desc += f"\n\n**Total Claimtime:** **{total}s**" if lines else "**Total Claimtime:** **0s**"
            embed = build_blue_embed("Claimtime", embed_desc)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)

    # ------------------------------------------------------
    @app_commands.command(name="claimtime_display", description="View all claimtime roles for this server")
    async def slash_claimtime_display(self, interaction: discord.Interaction):
        try:
            gid = str(interaction.guild.id)
            cfg = claimtime_config.get(gid, {})
            role_map = cfg.get("role_claimtimes", {})

            if not role_map:
                embed = build_blue_embed("Claimtime Roles", "No claimtime roles set for this server.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            lines = []
            for rid, data in role_map.items():
                role = interaction.guild.get_role(int(rid))
                role_text = role.name if role else f"Role ID {rid}"
                label = " (Override)" if isinstance(data, dict) and data.get("override") else ""
                seconds = data.get("seconds") if isinstance(data, dict) else data
                lines.append(f"**{role_text}** — `{seconds}` seconds{label}")

            embed = build_blue_embed("Claimtime Roles", "\n".join(lines))
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)

    # ------------------------------------------------------
    def parse_time(self, s: str) -> int:
        s = s.lower().strip()
        if s.endswith("s"):
            return int(s[:-1])
        elif s.endswith("m"):
            return int(s[:-1]) * 60
        elif s.endswith("h"):
            return int(s[:-1]) * 3600
        else:
            return int(s)

# ----------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Claimtime(bot))