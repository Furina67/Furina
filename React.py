import discord
from discord.ext import commands
import re

class MentionReact(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # 👇 Define each user's ID and their emoji list
        self.user_emoji_map = {
            832459817485860894: [  
                "<a:1000033780:1434781314124615712>",
                "<a:1000033779:1434781019562709092>",
                "<a:1000033774:1434780364844302378>",
                "<a:I_:1434780379872755812>",
                "<a:1000033778:1434780403113132124>",
                "<a:1000033775:1434781356335960175>"
            ],

            1192841625861357628: [  
                "<a:1000033783:1434794808916054116>",
                "<a:1000033775:1434781356335960175>",
                "<a:1000033784:1434794814578360320>",
                "<a:I_:1434780379872755812>",
                "<a:1000033785:1434794819682570301>",
                "<a:1000033786:1434794827068870768>"
            ],

            1281667086199951482: [  
                "<a:1000033881:1435650924428263495>",
                "<a:1000033882:1435650971437895903>",
                "<a:1000033883:1435651024294641804>",
                "<a:1000033884:1435651072562692117>",
                "<a:1000033885:1435651122105684082>",
                "<:1000033886:1435651165957263520>",
                "<a:1000033887:1435651209515241652>",
                "<a:1000033888:1435651250073894953>",
                "<a:1000033889:1435651292402942123>",
                "<a:1000033890:1435651334211899563>",
                "<a:1000033891:1435651385516363876>"
            ]
        }

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # 🚫 Ignore replies
        if message.reference is not None:
            return

        # ✅ Check mentions
        for user_id, emojis in self.user_emoji_map.items():
            if any(user.id == user_id for user in message.mentions):
                # Get the correct mention string
                mention_str = f"<@{user_id}>"
                mention_str_nick = f"<@!{user_id}>"

                # The message must *only* contain the mention (no other text)
                if message.content.strip() in [mention_str, mention_str_nick]:
                    for emoji in emojis:
                        try:
                            await message.add_reaction(emoji)
                        except discord.Forbidden:
                            print(f"Missing permission to add reaction: {emoji}")
                        except discord.HTTPException:
                            print(f"Failed to add reaction: {emoji}")
                return  # stop after reacting to first valid mention


async def setup(bot):
    await bot.add_cog(MentionReact(bot))