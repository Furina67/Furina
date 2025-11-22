import discord
from discord.ext import commands
import asyncio  # <-- import asyncio

# IDs
TEST_SERVER_ID = 1374715707220037662     # your test server ID
AUTHORIZED_USER_ID = 1281667086199951482  # user allowed to use $tip
ALLOWED_CATEGORY_IDS = [
1386644137411088437, 1399197925799891054, 1419868989412081755]  # list of allowed categories
VOUCH_CHANNEL_ID = 1374715708222472225     # your vouch channel ID

class Tip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not message.guild or message.guild.id != TEST_SERVER_ID:
            return

        if message.author.id != AUTHORIZED_USER_ID:
            return

        # Must be in allowed categories
        if not message.channel.category or message.channel.category.id not in ALLOWED_CATEGORY_IDS:
            return

        if not message.content.lower().startswith("$tip "):
            return

        try:
            parts = message.content.split()
            if len(parts) < 4 or not message.mentions:
                return await message.reply("❌ Usage: `$tip @user <amount> ltc`")

            payouter = message.author
            user = message.mentions[0]
            amount = float(parts[2].replace("$", ""))
            crypto = parts[3].lower()

            # Only ltc supported
            if crypto != "ltc":
                return

            # If less than 0.05$
            if amount < 0.05:
                return await message.channel.send("> No Need to Vouch\n> Close the Ticket")

            await asyncio.sleep(2)
            vouch_channel = f"<#{VOUCH_CHANNEL_ID}>"
            embed = discord.Embed(
                description=(
                    f"> Copy and Vouch here – {vouch_channel}\n"
                    f"> Legit got **{amount:.2f}$ {crypto}** from {payouter.mention}\n\n"
                    "No vouch = giveaway ban."
                ),
                color=discord.Color.blue()
            )
            embed.set_author(name=f"{user.display_name}", icon_url=user.display_avatar.url)

            # Button for copy
            class CopyVouchView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)

                @discord.ui.button(label="Copy to Clipboard", style=discord.ButtonStyle.primary)
                async def copy(self, interaction: discord.Interaction, button: discord.ui.Button):
                    vouch_text = f"Legit got {amount:.2f}$ {crypto} from {payouter.mention}"
                    await interaction.response.send_message(
                        f"{vouch_text}",
                        ephemeral=True
                    )

            await message.channel.send(
                content=user.mention,
                embed=embed,
                view=CopyVouchView()
            )

        except Exception as e:
            print(f"[Tip Error] {e}")

async def setup(bot):
    await bot.add_cog(Tip(bot))