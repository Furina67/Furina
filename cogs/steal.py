import discord
from discord.ext import commands
from discord.ui import View, Button
import aiohttp
from io import BytesIO
import re

class Steal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="steal")
    @commands.has_permissions(manage_emojis=True)
    async def steal(self, ctx):
        if not ctx.message.reference:
            return await ctx.reply("🔁 Reply to an emoji or sticker to steal it.")

        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)

        # Check for sticker
        sticker = ref.stickers[0] if ref.stickers else None

        # Check for custom emoji
        emoji_match = re.search(r"<(a?):(\w+):(\d+)>", ref.content)
        emoji = None
        if emoji_match:
            emoji = {
                "animated": emoji_match.group(1) == "a",
                "name": emoji_match.group(2),
                "id": emoji_match.group(3)
            }

        if not sticker and not emoji:
            return await ctx.reply("❌ Please reply to a valid sticker or custom emoji.")

        view = View()

        if sticker:
            # Send sticker image first
            file = await self.get_file_from_url(sticker.url)
            await ctx.send(file=file)

            class AddEmoji(Button):
                def __init__(self):
                    super().__init__(label="Add as Emoji", style=discord.ButtonStyle.green)

                async def callback(self, interaction: discord.Interaction):
                    await interaction.response.defer()
                    try:
                        data = await self.get_bytes(sticker.url)
                        new_emoji = await ctx.guild.create_custom_emoji(
                            name=sticker.name,
                            image=data
                        )
                        await interaction.followup.send(f"✅ Emoji added: {new_emoji}")
                    except Exception as e:
                        await interaction.followup.send(f"⚠️ Failed to add emoji:\n```{e}```")

                async def get_bytes(self, url):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            return await resp.read()

            # Button: Add as Sticker
            class AddSticker(Button):
                def __init__(self):
                    super().__init__(label="Add as Sticker", style=discord.ButtonStyle.blurple)

                async def callback(self, interaction: discord.Interaction):
                    await interaction.response.defer()
                    try:
                        data = await self.get_bytes(sticker.url)
                        discord_file = discord.File(BytesIO(data), filename="sticker.png")
                        new_sticker = await ctx.guild.create_sticker(
                            name=sticker.name,
                            description="Stolen with bot",
                            emoji="🙂",
                            file=discord_file
                        )
                        await interaction.followup.send(f"✅ Sticker added: {new_sticker.name}")
                    except Exception as e:
                        await interaction.followup.send(f"⚠️ Failed to add sticker:\n```{e}```")

                async def get_bytes(self, url):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            return await resp.read()

            view.add_item(AddEmoji())
            view.add_item(AddSticker())
            await ctx.reply("🎯 Choose how to steal this sticker:", view=view)

        if emoji:
            ext = "gif" if emoji["animated"] else "png"
            url = f"https://cdn.discordapp.com/emojis/{emoji['id']}.{ext}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.read()
            try:
                new_emoji = await ctx.guild.create_custom_emoji(
                    name=emoji["name"],
                    image=data
                )
                await ctx.reply(f"✅ Emoji added: {new_emoji}")
            except Exception as e:
                await ctx.reply(f"⚠️ Failed to add emoji:\n```{e}```")

    async def get_file_from_url(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.read()
        return discord.File(BytesIO(data), filename="sticker.png")


async def setup(bot):
    await bot.add_cog(Steal(bot))
