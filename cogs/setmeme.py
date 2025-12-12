import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import json
import random
import os

MEME_FILE = "meme_channels.json"
SUBREDDITS = ["memes", "funny", "wholesomememes", "memesirl", "dankmemes", "meme"]
OWNER_ID = 832459817485860894

class MemeAutoPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.meme_channels = self.load_meme_channels()
        self.sent_memes = set()
        self.failure_counts = {}
        self.send_memes.start()

    def cog_unload(self):
        self.send_memes.cancel()

    def load_meme_channels(self):
        if os.path.exists(MEME_FILE):
            with open(MEME_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_meme_channels(self):
        with open(MEME_FILE, "w") as f:
            json.dump(self.meme_channels, f, indent=4)

    @commands.command(name="setmeme")
    @commands.has_permissions(manage_channels=True)
    async def set_meme_channel(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        self.meme_channels[str(ctx.guild.id)] = channel.id
        self.save_meme_channels()
        await ctx.send(f"✅ Meme channel set to {channel.mention}")

    @commands.command(name="deletememe")
    @commands.has_permissions(manage_channels=True)
    async def delete_meme_channel(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.meme_channels:
            del self.meme_channels[guild_id]
            self.save_meme_channels()
            await ctx.send("🗑️ Meme channel removed.")
        else:
            await ctx.send("❌ No meme channel set for this server.")

    @tasks.loop(minutes=5)
    async def send_memes(self):
        meme_apis = [
            "https://meme-api.com/gimme/",
            "https://www.reddit.com/r/{subreddit}/hot.json?limit=50",
            "https://api.imgflip.com/get_memes"
        ]

        async with aiohttp.ClientSession() as session:
            for guild_id, channel_id in self.meme_channels.items():
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    continue

                subreddit = random.choice(SUBREDDITS)
                meme_data = None

                # --- Try each API with retries ---
                for attempt in range(3):
                    for api in meme_apis:
                        try:
                            if "meme-api.com" in api:
                                url = f"{api}{subreddit}"
                                async with session.get(url, timeout=10) as resp:
                                    data = await resp.json()
                                    meme_data = (
                                        data.get("url"),
                                        data.get("title"),
                                        data.get("postLink")
                                    )

                            elif "reddit.com" in api:
                                url = api.format(subreddit=subreddit)
                                headers = {"User-Agent": "DiscordBot/1.0"}
                                async with session.get(url, headers=headers, timeout=10) as resp:
                                    data = await resp.json()
                                    posts = data.get("data", {}).get("children", [])
                                    post = random.choice(posts)["data"]
                                    meme_data = (
                                        post.get("url_overridden_by_dest"),
                                        post.get("title"),
                                        f"https://reddit.com{post.get('permalink')}"
                                    )

                            elif "imgflip" in api:
                                async with session.get(api, timeout=10) as resp:
                                    data = await resp.json()
                                    meme = random.choice(data["data"]["memes"])
                                    meme_data = (
                                        meme.get("url"),
                                        meme.get("name"),
                                        "https://imgflip.com/"
                                    )

                            if meme_data[0]:
                                break

                        except Exception as e:
                            print(f"⚠️ API error (attempt {attempt+1}) from {api}: {e}")
                            await asyncio.sleep(2)

                    if meme_data:
                        break

                if not meme_data:
                    print(f"❌ Failed to fetch meme for guild {guild_id}.")
                    self.failure_counts[guild_id] = self.failure_counts.get(guild_id, 0) + 1

                    if self.failure_counts[guild_id] % 3 == 0:
                        owner = self.bot.get_user(OWNER_ID)
                        if owner:
                            try:
                                await owner.send(
                                    f"⚠️ Meme auto-post failed 3 times in guild `{guild_id}`.\n"
                                    f"Possible API outage."
                                )
                            except:
                                pass
                    continue

                meme_url, title, post_link = meme_data

                if meme_url in self.sent_memes:
                    continue

                self.sent_memes.add(meme_url)
                if len(self.sent_memes) > 100:
                    self.sent_memes.pop()

                embed = discord.Embed(
                    title=title or "Random Meme 😂",
                    url=post_link,
                    color=discord.Color.random()
                )
                embed.set_image(url=meme_url)
                embed.set_footer(text=f"From r/{subreddit}")

                try:
                    await channel.send(embed=embed)
                except Exception as e:
                    print(f"❌ Could not send meme in guild {guild_id}: {e}")

    @send_memes.before_loop
    async def before_memes(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(MemeAutoPost(bot))
