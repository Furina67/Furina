import discord
from discord.ext import commands
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import random
import math

class Ship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_avatar(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return Image.open(BytesIO(await resp.read())).convert("RGBA")

    @commands.command()
    async def ship(self, ctx, user1: discord.User = None, user2: discord.User = None):
        if not user1 or not user2:
            return await ctx.send("Please mention two users to ship! ❤️")

        compatibility = random.randint(0, 100)

        # Fetch avatars
        avatar1 = await self.fetch_avatar(user1.display_avatar.url)
        avatar2 = await self.fetch_avatar(user2.display_avatar.url)

        avatar_size = 170
        avatar1 = avatar1.resize((avatar_size, avatar_size))
        avatar2 = avatar2.resize((avatar_size, avatar_size))

        # Make circular mask
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        avatar1.putalpha(mask)
        avatar2.putalpha(mask)

        # Create background
        width, height = 800, 500
        img = Image.new("RGBA", (width, height), (25, 25, 25, 255))
        draw = ImageDraw.Draw(img)

        # Fonts
        try:
            font_big = ImageFont.truetype("arial.ttf", 48)
            font_small = ImageFont.truetype("arial.ttf", 34)
        except:
            font_big = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Positions
        left_x = 140
        right_x = width - 310
        y_avatar = 160
        img.paste(avatar1, (left_x, y_avatar), avatar1)
        img.paste(avatar2, (right_x, y_avatar), avatar2)

        # Draw usernames
        draw.text((left_x + avatar_size // 2, y_avatar - 40), user1.name, font=font_big, fill="white", anchor="mm")
        draw.text((right_x + avatar_size // 2, y_avatar - 40), user2.name, font=font_big, fill="white", anchor="mm")

        # Draw small heart between them
        heart_center_x = width // 2
        heart_center_y = y_avatar + 85
        heart_size = 25
        heart_color = (255, 80, 80)
        self.draw_heart(draw, heart_center_x, heart_center_y, heart_size, heart_color)

        # Draw bar
        bar_w, bar_h = 500, 40
        bar_x, bar_y = (width - bar_w) // 2, 350
        draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=20, fill=(80, 80, 80))
        fill_w = int(bar_w * (compatibility / 100))
        draw.rounded_rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), radius=20, fill=heart_color)

        # Compatibility text
        text = f"Compatibility: {compatibility}%"
        draw.text((width // 2, 420), text, font=font_small, fill="white", anchor="mm")

        # Save to buffer
        buffer = BytesIO()
        img.save(buffer, "PNG")
        buffer.seek(0)

        # Send
        embed = discord.Embed(
            title="💕 Love Calculator 💕",
            description=f"{user1.mention} ❤️ {user2.mention}\n**Compatibility:** {compatibility}%",
            color=discord.Color.pink(),
        )
        embed.set_image(url="attachment://ship.png")
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed, file=discord.File(buffer, "ship.png"))

    def draw_heart(self, draw, x, y, size, color):
        """Draws a properly scaled heart."""
        points = []
        for angle in range(0, 360, 1):
            t = math.radians(angle)
            px = size * 16 * math.sin(t)**3
            py = -size * (13 * math.cos(t) - 5 * math.cos(2*t) -
                          2 * math.cos(3*t) - math.cos(4*t))
            points.append((x + px / 16 * 1.2, y + py / 16 * 1.2))
        draw.polygon(points, fill=color)

async def setup(bot):
    await bot.add_cog(Ship(bot))
