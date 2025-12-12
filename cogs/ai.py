import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import urllib.parse
import os

GROQ_API_KEY = ("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
CHAR_LIMIT_PLAIN = 2000
DDG_ENDPOINT = "https://api.duckduckgo.com/"


class RealtimeAICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    async def groq_complete(self, system_prompt: str, user_prompt: str):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        try:
            async with self.session.post(url, json=payload, headers=headers, timeout=120) as resp:
                try:
                    data = await resp.json()
                except:
                    return "I couldn't parse the AI response."

                if "error" in data:
                    return "There was an error contacting the AI model."

                try:
                    return data["choices"][0]["message"]["content"]
                except:
                    return "The AI returned an unexpected response."
        except asyncio.TimeoutError:
            return "AI request timed out."

    async def fetch_ddg(self, query: str):
        params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
        async with self.session.get(DDG_ENDPOINT, params=params) as resp:
            if resp.status != 200:
                return {}
            try:
                return await resp.json()
            except:
                return {}

    async def wiki_search_title(self, query: str):
        url = "https://en.wikipedia.org/w/api.php"
        params = {"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 1}
        async with self.session.get(url, params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            hits = data.get("query", {}).get("search", [])
            return hits[0].get("title") if hits else None

    async def wiki_summary(self, title: str):
        if not title:
            return None
        safe_title = urllib.parse.quote(title)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe_title}"
        async with self.session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return {
                "title": data.get("title"),
                "extract": data.get("extract"),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page")
            }

    async def search_and_collect(self, query: str, max_chars=3000):
        ddg = await self.fetch_ddg(query)
        snippets = []

        if ddg:
            abstract = ddg.get("AbstractText", "")
            if abstract:
                snippets.append(("DuckDuckGo Abstract", abstract))

            for topic in ddg.get("RelatedTopics", []):
                if isinstance(topic, dict):
                    text = topic.get("Text") or topic.get("Name")
                    if text:
                        snippets.append(("DuckDuckGo Related", text))
                if sum(len(s) for _, s in snippets) > max_chars:
                    break

        wiki_title = await self.wiki_search_title(query)
        wiki = None

        if wiki_title:
            wiki = await self.wiki_summary(wiki_title)
            if wiki and wiki.get("extract"):
                snippets.append(("Wikipedia", wiki.get("extract")))

        combined = []
        total_len = 0

        for source, text in snippets:
            if not text:
                continue
            if total_len + len(text) > max_chars:
                remaining = max_chars - total_len
                if remaining <= 0:
                    break
                text = text[:remaining] + "..."
            combined.append(f"[{source}]\n{text}")
            total_len += len(text)
            if total_len >= max_chars:
                break

        return {
            "combined": "\n\n".join(combined) if combined else None,
            "wiki": wiki,
            "ddg": ddg
        }

    async def send_smart(self, ctx, text: str):
        if not text:
            text = "I couldn't find an answer."

        if len(text) <= CHAR_LIMIT_PLAIN:
            if isinstance(ctx, discord.Interaction):
                await ctx.followup.send(text)
            else:
                await ctx.reply(text)
        else:
            embed = discord.Embed(description=text)
            if isinstance(ctx, discord.Interaction):
                await ctx.followup.send(embed=embed)
            else:
                await ctx.reply(embed=embed)

    @commands.command(name="ai")
    async def ai_prefix(self, ctx, *, prompt: str):
        async with ctx.typing():
            system = (
                "You are an advanced assistant. Provide accurate, well-formatted replies suitable for Discord."
            )
            reply = await self.groq_complete(system, prompt)
        await self.send_smart(ctx, reply)

    @app_commands.command(name="ai", description="Ask the AI anything.")
    async def ai_slash(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        system = (
            "You are an advanced assistant. Provide accurate, well-formatted replies suitable for Discord."
        )
        reply = await self.groq_complete(system, prompt)
        await self.send_smart(interaction, reply)

    @commands.command(name="ask")
    async def ask_prefix(self, ctx, *, query: str):
        async with ctx.typing():
            collected = await self.search_and_collect(query)
            if collected["combined"]:
                system = "You summarize search results into a short, accurate answer."
                user_prompt = (
                    f"User asked: {query}\n\nSearch snippets:\n\n"
                    f"{collected['combined']}\n\nProvide a concise answer."
                )
                reply = await self.groq_complete(system, user_prompt)
            else:
                reply = "I couldn't find live results for that query."
        await self.send_smart(ctx, reply)

    @app_commands.command(name="ask", description="Ask something and the bot will search the web.")
    async def ask_slash(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        collected = await self.search_and_collect(query)

        if collected["combined"]:
            system = "You summarize search results into a short, accurate answer."
            user_prompt = (
                f"User asked: {query}\n\nSearch snippets:\n\n"
                f"{collected['combined']}\n\nProvide a concise answer."
            )
            reply = await self.groq_complete(system, user_prompt)
        else:
            reply = "I couldn't find live results for that query."

        await self.send_smart(interaction, reply)


async def setup(bot):
    await bot.add_cog(RealtimeAICog(bot))
