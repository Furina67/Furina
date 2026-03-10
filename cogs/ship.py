import discord
from discord.ext import commands
from discord import app_commands
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import aiohttp
import os
import random
import math

ASSETS_PATH = "/home/container/assets"


class Ship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

        self.quotes = [
            "The tides of Fontaine whisper your fate.",
            "Even the Oratrice acknowledges this union.",
            "Hydro energy flows between you.",
            "Furina would absolutely dramatize this.",
            "Neuvillette silently approves.",
            "A bond blessed by Fontaine.",
            "Destiny flows like water.",
            "Judgment has been delivered."
        ]

    async def cog_unload(self):
        await self.session.close()

    async def fetch_avatar(self, url):
        async with self.session.get(url) as resp:
            data = await resp.read()
        return Image.open(BytesIO(data)).convert("RGBA")

    @commands.hybrid_command(name="ship", description="Fontaine love compatibility")
    @app_commands.describe(user1="First user", user2="Second user")
    async def ship(self, ctx, user1: discord.User, user2: discord.User):

        if user1.id == user2.id:
            return await ctx.send(
                "You cannot ship someone with themselves.",
                allowed_mentions=discord.AllowedMentions.none()
            )

        compatibility = abs(hash(f"{user1.id}{user2.id}")) % 101
        quote = random.choice(self.quotes)

        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            loading = await ctx.send("The waters of Fontaine are calculating...")

        avatar1 = await self.fetch_avatar(user1.display_avatar.url)
        avatar2 = await self.fetch_avatar(user2.display_avatar.url)

        size = 180
        avatar1 = avatar1.resize((size, size))
        avatar2 = avatar2.resize((size, size))

        mask = Image.new("L", (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size, size), fill=255)
        avatar1.putalpha(mask)
        avatar2.putalpha(mask)

        width, height = 900, 520

        backgrounds = [
            os.path.join(ASSETS_PATH, f)
            for f in os.listdir(ASSETS_PATH)
            if f.lower().endswith(".jpg")
        ]

        if not backgrounds:
            return await ctx.send("No background images found.")

        bg = Image.open(random.choice(backgrounds)).convert("RGBA")
        bg = bg.resize((width, height))
        bg = bg.filter(ImageFilter.GaussianBlur(3))

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 40))
        bg = Image.alpha_composite(bg, overlay)

        img = bg.copy()
        draw = ImageDraw.Draw(img)

        left_x = 180
        right_x = width - 360
        y_avatar = 150

        img.paste(avatar1, (left_x, y_avatar), avatar1)
        img.paste(avatar2, (right_x, y_avatar), avatar2)

        try:
            font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        except:
            font_big = ImageFont.load_default()
            font_small = ImageFont.load_default()

        draw.text((left_x + size // 2, y_avatar - 50),
                  user1.display_name, font=font_big, fill="white", anchor="mm")

        draw.text((right_x + size // 2, y_avatar - 50),
                  user2.display_name, font=font_big, fill="white", anchor="mm")

        # Heart
        heart_x = width // 2
        heart_y = y_avatar + 85

        self.draw_real_heart(draw, heart_x, heart_y, 72, (255, 255, 255))
        self.draw_real_heart(draw, heart_x, heart_y, 70, (255, 30, 30))

        # Progress bar
        bar_width = 600
        bar_height = 35
        bar_x = (width - bar_width) // 2
        bar_y = 370

        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + bar_width, bar_y + bar_height),
            radius=25,
            fill=(40, 40, 40)
        )

        fill_width = int(bar_width * (compatibility / 100))

        if compatibility <= 30:
            bar_color = (180, 60, 60)
        elif compatibility <= 70:
            bar_color = (220, 50, 50)
        else:
            bar_color = (255, 40, 40)

        if fill_width > 0:
            draw.rounded_rectangle(
                (bar_x, bar_y, bar_x + fill_width, bar_y + bar_height),
                radius=25,
                fill=bar_color
            )

        draw.text((width // 2, bar_y + bar_height + 60),
                  f"{compatibility}% Compatibility",
                  font=font_small, fill="white", anchor="mm")

        buffer = BytesIO()
        img.save(buffer, "PNG")
        buffer.seek(0)

        file = discord.File(buffer, filename="ship.png")

        view = discord.ui.LayoutView()
        container = discord.ui.Container()

        container.add_item(
            discord.ui.TextDisplay(
                f"## Hydro Resonance Reading\n\n"
                f"{user1.display_name} Ã— {user2.display_name}\n\n"
                f"*{quote}*"
            )
        )

        container.add_item(discord.ui.Separator())

        gallery = discord.ui.MediaGallery()
        gallery.add_item(media="attachment://ship.png")
        container.add_item(gallery)

        view.add_item(container)

        if ctx.interaction:
            await ctx.interaction.followup.send(
                view=view,
                file=file,
                allowed_mentions=discord.AllowedMentions.none()
            )
        else:
            await loading.delete()
            await ctx.send(
                view=view,
                file=file,
                allowed_mentions=discord.AllowedMentions.none()
            )

    @ship.error
    async def ship_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You must mention two users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("I couldn't find that user.")
        else:
            await ctx.send("Something went wrong while calculating compatibility.")

    def draw_real_heart(self, draw, x, y, size, color):
        points = []
        for t in range(0, 360):
            angle = math.radians(t)
            px = size * 16 * math.sin(angle) ** 3
            py = -size * (
                13 * math.cos(angle)
                - 5 * math.cos(2 * angle)
                - 2 * math.cos(3 * angle)
                - math.cos(4 * angle)
            )
            points.append((x + px / 16, y + py / 16))
        draw.polygon(points, fill=color)


async def setup(bot):
    await bot.add_cog(Ship(bot))