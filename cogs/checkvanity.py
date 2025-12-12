import logging
import discord
from discord.ext import commands
import aiohttp
import asyncio
import traceback

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
        try:
            if not code:
                return await ctx.reply("Please provide a vanity code. Example: `.checkvanity xyz`", mention_author=False)

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
                                f"Vanity `{code}` is available.",
                                mention_author=False
                            )

                        if status != 200:
                            return await ctx.reply(f"API error: {status}. Try again later.", mention_author=False)

                        data = await resp.json()

                except asyncio.TimeoutError:
                    return await ctx.reply("Request timed out. Try again.", mention_author=False)
                except Exception as e:
                    return await ctx.reply(f"Request failed: {e}", mention_author=False)

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

            pretty_features = [f"- {f.replace('_', ' ').title()}" for f in sorted(feature_list)]
            feature_text = "\n".join(pretty_features) if pretty_features else "No special features."

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

            embed = discord.Embed(
                title=f"{server_name}'s Vanity Information",
                description=f"The vanity code `{code}` is taken.",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="About",
                value=(
                    f"Server Name: {server_name}\n"
                    f"Server ID: `{server_id}`\n"
                    f"Boosts: `{boost_count}`\n"
                    f"Boost Level: `{boost_tier}`"
                ),
                inline=False
            )

            for i, chunk in enumerate(feature_chunks):
                embed.add_field(
                    name="Features" if i == 0 else f"Features (cont. {i+1})",
                    value=chunk,
                    inline=False
                )

            embed.add_field(
                name="Extras",
                value=(
                    f"Verification: `{guild.get('verification_level', 'N/A')}`\n"
                    f"NSFW Level: `{guild.get('nsfw_level', 'N/A')}`\n"
                    f"2FA Requirement: `{'Required' if guild.get('mfa_level', 0) else 'Not Required'}`"
                ),
                inline=False
            )

            embed.add_field(
                name="Members",
                value=(
                    f"Total Members: `{approximate_member_count}`\n"
                    f"Online Members: `{approximate_presence_count}`"
                ),
                inline=False
            )

            if icon:
                embed.set_thumbnail(url=f"https://cdn.discordapp.com/icons/{server_id}/{icon}.png?size=1024")
            if banner:
                embed.set_image(url=f"https://cdn.discordapp.com/banners/{server_id}/{banner}?size=1024")

            embed.set_footer(
                text=f"Requested by {ctx.author}",
                icon_url=ctx.author.display_avatar.url
            )

            await ctx.reply(embed=embed, mention_author=False)

        except Exception:
            logger.error("Unhandled exception in checkvanity:\n" + traceback.format_exc())
            await ctx.reply("An unexpected error occurred. Check logs for details.", mention_author=False)


async def setup(bot):
    await bot.add_cog(CheckVanity(bot))
