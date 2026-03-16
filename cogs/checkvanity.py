import discord
from discord.ext import commands
import aiohttp
import asyncio


class CheckVanityView(discord.ui.LayoutView):
    def __init__(self, author: discord.Member, data: dict, code: str):
        super().__init__(timeout=None)

        guild = data.get("guild", {})
        server_name = guild.get("name", "Unknown")
        server_id = guild.get("id", "N/A")
        boosts = guild.get("premium_subscription_count", 0)
        tier = guild.get("premium_tier", 0)
        verification = guild.get("verification_level", "N/A")
        nsfw = guild.get("nsfw_level", "N/A")
        mfa = "Required" if guild.get("mfa_level", 0) else "Not Required"

        member_count = data.get("approximate_member_count", "N/A")
        online_count = data.get("approximate_presence_count", "N/A")

        features = guild.get("features", [])
        icon = guild.get("icon")
        banner = guild.get("banner")

        container = discord.ui.Container()

        container.add_item(
            discord.ui.Section(
                discord.ui.TextDisplay(
                    f"## {server_name}\n"
                    f"Vanity `{code}` is taken."
                ),
                accessory=discord.ui.Thumbnail(
                    f"https://cdn.discordapp.com/icons/{server_id}/{icon}.png?size=1024"
                ) if icon else None
            )
        )

        container.add_item(discord.ui.Separator())

        container.add_item(
            discord.ui.TextDisplay(
                f"### Server\n"
                f"ID: `{server_id}`\n"
                f"Boosts: `{boosts}`\n"
                f"Boost Level: `{tier}`"
            )
        )

        container.add_item(discord.ui.Separator())

        container.add_item(
            discord.ui.TextDisplay(
                f"### Members\n"
                f"Total: `{member_count}`\n"
                f"Online: `{online_count}`"
            )
        )

        if features:
            container.add_item(discord.ui.Separator())
            feature_text = "\n".join(
                f.replace("_", " ").title() for f in sorted(features)
            )
            container.add_item(
                discord.ui.TextDisplay(
                    f"### Features\n{feature_text}"
                )
            )

        container.add_item(discord.ui.Separator())

        container.add_item(
            discord.ui.TextDisplay(
                f"### Security\n"
                f"Verification Level: `{verification}`\n"
                f"NSFW Level: `{nsfw}`\n"
                f"2FA Requirement: `{mfa}`"
            )
        )

        if banner:
            container.add_item(discord.ui.Separator())
            gallery = discord.ui.MediaGallery()
            gallery.add_item(
                media=f"https://cdn.discordapp.com/banners/{server_id}/{banner}?size=1024"
            )
            container.add_item(gallery)

        container.add_item(discord.ui.Separator())

        container.add_item(
            discord.ui.TextDisplay(
                f"Requested by {author.display_name}"
            )
        )

        self.add_item(container)


class CheckVanity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="checkvanity",
        description="Check if a Discord vanity code is taken"
    )
    async def check_vanity(self, ctx: commands.Context, code: str = None):

        if not code:
            return await ctx.send(
                "Please provide a vanity code. Example: `checkvanity dpy`"
            )

        code = code.strip().lower()
        url = f"https://discord.com/api/v10/invites/{code}?with_counts=true"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as resp:

                    if resp.status == 404:
                        return await ctx.send(
                            f"Vanity `{code}` is available."
                        )

                    if resp.status != 200:
                        return await ctx.send(
                            f"API error: {resp.status}. Try again later."
                        )

                    data = await resp.json()

            except asyncio.TimeoutError:
                return await ctx.send("Request timed out. Try again.")

        view = CheckVanityView(ctx.author, data, code)

        if ctx.interaction:
            await ctx.interaction.response.send_message(view=view)
        else:
            await ctx.send(view=view)


async def setup(bot):
    await bot.add_cog(CheckVanity(bot))