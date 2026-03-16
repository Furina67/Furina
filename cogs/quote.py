import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import aiohttp
import io
import textwrap


class Quote(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        self.BOT_NAME = "Furina"

    async def generate_quote_image(self, user, text):
        WIDTH, HEIGHT = 1200, 600
        LEFT_WIDTH = 550
        FADE_WIDTH = 250

        async with aiohttp.ClientSession() as session:
            async with session.get(user.display_avatar.url) as resp:
                avatar_bytes = await resp.read()

        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGB")

        bg = avatar.resize((WIDTH, HEIGHT))
        bg = bg.filter(ImageFilter.GaussianBlur(30))

        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 140))
        bg = bg.convert("RGBA")
        bg = Image.alpha_composite(bg, overlay)

        avatar_left = avatar.resize((LEFT_WIDTH, HEIGHT))

        mask = Image.new("L", (LEFT_WIDTH, HEIGHT), 255)
        mask_data = mask.load()

        for x in range(LEFT_WIDTH):
            if x > LEFT_WIDTH - FADE_WIDTH:
                distance = x - (LEFT_WIDTH - FADE_WIDTH)
                alpha = int(255 * (1 - distance / FADE_WIDTH))
                for y in range(HEIGHT):
                    mask_data[x, y] = alpha

        avatar_rgba = avatar_left.convert("RGBA")
        avatar_rgba.putalpha(mask)
        bg.paste(avatar_rgba, (0, 0), avatar_rgba)

        draw = ImageDraw.Draw(bg)

        max_font_size = 55
        min_font_size = 28
        spacing = 12

        quote_area_start = LEFT_WIDTH
        quote_area_width = WIDTH - LEFT_WIDTH
        center_x = quote_area_start + quote_area_width // 2
        center_y = HEIGHT // 2

        safe_top = 150
        safe_bottom = HEIGHT - 200
        max_height = safe_bottom - safe_top

        font_size = max_font_size

        while font_size >= min_font_size:
            quote_font = ImageFont.truetype(self.FONT_PATH, font_size)
            wrapped = textwrap.fill(text, width=28)

            bbox = draw.multiline_textbbox((0, 0), wrapped, font=quote_font, spacing=spacing)
            text_height = bbox[3] - bbox[1]

            if text_height <= max_height:
                break

            font_size -= 2

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = center_x - text_width // 2
        text_y = center_y - text_height // 2

        name_font = ImageFont.truetype(self.FONT_PATH, int(font_size * 0.7))
        big_quote_font = ImageFont.truetype(self.FONT_PATH, 160)
        watermark_font = ImageFont.truetype(self.FONT_PATH, 26)

        draw.text(
            (WIDTH // 2 - 40, 40),
            "â€œ",
            font=big_quote_font,
            fill=(150, 150, 150, 70)
        )

        draw.multiline_text(
            (text_x, text_y),
            wrapped,
            font=quote_font,
            fill=(40, 40, 40),
            spacing=spacing,
            align="center"
        )

        draw.text(
            (WIDTH - 140, HEIGHT - 160),
            "â€",
            font=big_quote_font,
            fill=(150, 150, 150, 70)
        )

        name_text = f"- {user.name}"
        name_bbox = draw.textbbox((0, 0), name_text, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]

        draw.text(
            (center_x - name_width // 2, text_y + text_height + 30),
            name_text,
            font=name_font,
            fill=(110, 110, 110)
        )

        watermark_bbox = draw.textbbox((0, 0), f"{self.BOT_NAME}", font=watermark_font)
        watermark_width = watermark_bbox[2] - watermark_bbox[0]

        draw.text(
            (WIDTH - watermark_width - 30, HEIGHT - 45),
            f"{self.BOT_NAME}",
            font=watermark_font,
            fill=(120, 120, 120, 120)
        )

        buffer = io.BytesIO()
        bg.convert("RGB").save(buffer, format="PNG")
        buffer.seek(0)

        return buffer

    @app_commands.command(name="quote", description="Create quote image")
    @app_commands.describe(text="Quote text")
    async def slash_quote(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        buffer = await self.generate_quote_image(interaction.user, text)
        await interaction.followup.send(file=discord.File(buffer, "quote.png"))

    @commands.command(name="quote")
    async def prefix_quote(self, ctx: commands.Context):
        if not ctx.message.reference:
            return await ctx.reply("Reply to a message to quote it.", mention_author=False)

        try:
            replied = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except:
            return await ctx.reply("Couldn't fetch that message.", mention_author=False)

        if not replied.content:
            return await ctx.reply("That message has no text to quote.", mention_author=False)

        buffer = await self.generate_quote_image(replied.author, replied.content)
        await ctx.reply(file=discord.File(buffer, "quote.png"), mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Quote(bot))