import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import json
import random
import os

MEME_FILE = "meme_channels.json"
SUBREDDITS = ["memes", "funny", "wholesomememes", "memesirl", "dankmemes"]
OWNER_ID = 832459817485860894  # 👈 Replace this with your Discord ID

class MemeAutoPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.meme_channels = self.load_meme_channels()
        self.sent_memes = set()
        self.failure_counts = {}
        self.send_memes.start()

    def cog_unload(self):
        self.send_memes.cancel()

    # -------------------
    # JSON Data Handling
    # -------------------
    def load_meme_channels(self):
        if os.path.exists(MEME_FILE):
            with open(MEME_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_meme_channels(self):
        with open(MEME_FILE, "w") as f:
            json.dump(self.meme_channels, f, indent=4)

    # -------------------
    # Commands
    # -------------------
    @commands.command(name="setmeme")
    @commands.has_permissions(manage_channels=True)
    async def set_meme_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel where memes will be automatically posted."""
        if not channel:
            channel = ctx.channel
        self.meme_channels[str(ctx.guild.id)] = channel.id
        self.save_meme_channels()
        await ctx.send(f"✅ Meme channel set to {channel.mention}")

    @commands.command(name="deletememe")
    @commands.has_permissions(manage_channels=True)
    async def delete_meme_channel(self, ctx):
        """Delete the meme channel for this server."""
        guild_id = str(ctx.guild.id)
        if guild_id in self.meme_channels:
            del self.meme_channels[guild_id]
            self.save_meme_channels()
            await ctx.send("🗑️ Meme channel removed successfully.")
        else:
            await ctx.send("❌ No meme channel was set for this server.")

    # -------------------
    # Background Task
    # -------------------
    @tasks.loop(minutes=5)
    async def send_memes(self):
        """Automatically sends memes every 5 minutes."""

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

                # --- Try multiple APIs with retries ---
                for attempt in range(3):
                    for api in meme_apis:
                        try:
                            # 1️⃣ Meme API
                            if "meme-api.com" in api:
                                url = f"{api}{subreddit}"
                                async with session.get(url, timeout=10) as resp:
                                    if resp.status != 200:
                                        raise Exception(f"Bad status: {resp.status}")
                                    data = await resp.json()
                                    meme_url = data.get("url")
                                    title = data.get("title")
                                    post_link = data.get("postLink")

                            # 2️⃣ Reddit API
                            elif "reddit.com" in api:
                                url = api.format(subreddit=subreddit)
                                headers = {"User-Agent": "DiscordBot/1.0"}
                                async with session.get(url, headers=headers, timeout=10) as resp:
                                    if resp.status != 200:
                                        raise Exception(f"Bad status: {resp.status}")
                                    data = await resp.json()
                                    posts = data.get("data", {}).get("children", [])
                                    if not posts:
                                        raise Exception("No posts found on Reddit.")
                                    post = random.choice(posts)["data"]
                                    meme_url = post.get("url_overridden_by_dest")
                                    title = post.get("title")
                                    post_link = f"https://reddit.com{post.get('permalink')}"

                            # 3️⃣ Imgflip API
                            elif "imgflip" in api:
                                async with session.get(api, timeout=10) as resp:
                                    if resp.status != 200:
                                        raise Exception(f"Bad status: {resp.status}")
                                    data = await resp.json()
                                    memes = data.get("data", {}).get("memes", [])
                                    if not memes:
                                        raise Exception("No memes found on Imgflip.")
                                    meme = random.choice(memes)
                                    meme_url = meme.get("url")
                                    title = meme.get("name")
                                    post_link = "https://imgflip.com/"

                            else:
                                continue

                            if not meme_url:
                                raise Exception("No meme URL found.")

                            meme_data = (meme_url, title, post_link)
                            break

                        except Exception as e:
                            print(f"⚠️ API error (attempt {attempt+1}) on {api}: {e}")
                            await asyncio.sleep(2)

                    if meme_data:
                        break

                # --- Failed after all retries ---
                if not meme_data:
                    print(f"❌ Failed to fetch meme for guild {guild_id} after retries.")
                    self.failure_counts[guild_id] = self.failure_counts.get(guild_id, 0) + 1

                    # DM alert to owner every 3 consecutive failures
                    if self.failure_counts[guild_id] % 3 == 0:
                        owner = self.bot.get_user(OWNER_ID)
                        if owner:
                            try:
                                await owner.send(
                                    f"⚠️ Meme auto-post failed 3 times in a row for guild ID `{guild_id}`.\n"
                                    f"All meme APIs returned errors.\nPlease check if meme-api.com or Reddit is blocked or down."
                                )
                            except:
                                print("⚠️ Could not DM the owner about meme failure.")
                    continue

                meme_url, title, post_link = meme_data

                # --- Prevent duplicates ---
                if meme_url in self.sent_memes:
                    continue
                self.sent_memes.add(meme_url)
                if len(self.sent_memes) > 100:
                    self.sent_memes.pop()

                # --- Send meme embed ---
                embed = discord.Embed(
                    title=title or "Random Meme 😂",
                    url=post_link,
                    color=discord.Color.random()
                )
                embed.set_image(url=meme_url)
                embed.set_footer(text=f"From r/{subreddit}")

                try:
                    await channel.send(embed=embed)
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"❌ Failed to send meme in {guild_id}: {e}")

    @send_memes.before_loop
    async def before_memes(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(MemeAutoPost(bot))