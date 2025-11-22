import logging
import discord
from discord.ext import commands
import aiohttp
import traceback

# configure logging (prints to container console)
logger = logging.getLogger("checkvanity")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

class CheckVanity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="checkvanity")
    async def check_vanity(self, ctx, code: str = None):
        """Check a server's vanity URL (example: .checkvanity kamiko). Replies without ping."""
        try:
            if not code:
                return await ctx.reply("❌ Please provide a vanity code. Example: `.checkvanity kamiko`", mention_author=False)

            code = code.strip().lower()
            url = f"https://discord.com/api/v10/invites/{code}?with_counts=true&with_expiration=true"

            logger.info(f"Checking vanity: {code} -> {url} (requested by {ctx.author})")

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=10) as resp:
                        status = resp.status
                        logger.info(f"HTTP status for {code}: {status}")
                        if status == 404:
                            return await ctx.reply(
                                f"<a:1000033595:1433520780620075123> Vanity `{code}` not found (available).",
                                mention_author=False
                            )
                        if status != 200:
                            text = await resp.text()
                            logger.error(f"Unexpected response {status} for {code}: {text[:200]}")
                            return await ctx.reply(f"⚠️ API error: {status}. Try again later.", mention_author=False)

                        data = await resp.json()
                except asyncio.TimeoutError:
                    logger.exception("Request timed out")
                    return await ctx.reply("⚠️ Request timed out. Try again.", mention_author=False)
                except Exception as e:
                    logger.exception("HTTP request failed")
                    return await ctx.reply(f"⚠️ Request failed: {e}", mention_author=False)

            # --- parse safely ---
            guild = data.get("guild", {}) or {}
            approximate_member_count = data.get("approximate_member_count", "N/A")
            approximate_presence_count = data.get("approximate_presence_count", "N/A")

            server_name = guild.get("name", "Unknown")
            server_id = guild.get("id", "N/A")
            feature_list = guild.get("features", []) or []
            boost_count = guild.get("premium_subscription_count", "N/A")
            boost_tier = guild.get("premium_tier", "N/A")
            banner = guild.get("banner")
            icon = guild.get("icon")

            # emojis (your server emojis)
            sparkle = "<a:1000033595:1433520780620075123>"
            boost_emoji = "<:1000033519:1433187447944253521>"
            member_emoji = "<:1000033535:1433229292564906004>"
            extra_emoji = sparkle

            # build feature text with safe newlines and sorting
            pretty_features = [f"{sparkle} {f.replace('_', ' ').title()}" for f in sorted(feature_list)]
            feature_text = "\n".join(pretty_features) if pretty_features else "No special features."

            # create embed
            embed = discord.Embed(
                title=f"{sparkle} {server_name}'s Information",
                description=f"The vanity code `{code}` is **taken.**" if guild else f"The vanity code `{code}` is **not available**.",
                color=discord.Color.blue()
            )

            embed.add_field(
                name=f"{boost_emoji} About",
                value=(
                    f"{sparkle} **Server Name:** {server_name}\n"
                    f"{sparkle} **Server ID:** `{server_id}`\n"
                    f"{boost_emoji} **Boosts:** `{boost_count}`\n"
                    f"{boost_emoji} **Boost Level:** `{boost_tier}`"
                ),
                inline=False
            )

            # features may be long — split safely into chunks <= 1024
            def chunk_text(text, limit=1024):
                chunks = []
                current = ""
                for line in text.splitlines():
                    if len(current) + len(line) + 1 > limit:
                        chunks.append(current)
                        current = ""
                    current += line + "\n"
                if current:
                    chunks.append(current)
                return chunks

            feature_chunks = chunk_text(feature_text)
            for i, c in enumerate(feature_chunks):
                name = f"{sparkle} Features" if i == 0 else f"{sparkle} Features (cont. {i+1})"
                embed.add_field(name=name, value=c, inline=False)

            embed.add_field(
                name=f"{extra_emoji} Extras",
                value=(
                    f"{extra_emoji} **Verification:** `{guild.get('verification_level', 'N/A')}`\n"
                    f"{extra_emoji} **NSFW Level:** `{guild.get('nsfw_level', 'N/A')}`\n"
                    f"{extra_emoji} **2FA Requirement:** `{'Required' if guild.get('mfa_level', 0) else 'Not Required'}'"
                ),
                inline=False
            )

            embed.add_field(
                name=f"{member_emoji} Member",
                value=(
                    f"{member_emoji} **Total Members:** `{approximate_member_count}`\n"
                    f"{member_emoji} **Online Members:** `{approximate_presence_count}`"
                ),
                inline=False
            )

            # visuals: icon + banner (banner at bottom)
            if icon:
                embed.set_thumbnail(url=f"https://cdn.discordapp.com/icons/{server_id}/{icon}.png?size=1024")
            if banner:
                embed.set_image(url=f"https://cdn.discordapp.com/banners/{server_id}/{banner}?size=1024")

            embed.set_footer(text=f"Checked via Discord Invite API | Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            # log full stack and show user friendly message
            logger.error("Unhandled exception in checkvanity command:\n" + traceback.format_exc())
            await ctx.reply("❌ An unexpected error occurred. Check the bot console for details.", mention_author=False)

async def setup(bot):
    await bot.add_cog(CheckVanity(bot))