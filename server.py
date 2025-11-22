import discord
from discord.ext import commands

# Bot owner IDs
BOT_OWNER_IDS = [832459817485860894, 493145844166426624, 1356075369853223033, 1256262917314318468]


class ServerPaginator(discord.ui.View):
    def __init__(self, pages, user: discord.User):
        super().__init__(timeout=180)
        self.pages = pages
        self.current_page = 0
        self.user = user

    async def update_message(self, interaction: discord.Interaction):
        embed = self.pages[self.current_page]
        # Disable navigation buttons appropriately
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page == len(self.pages) - 1
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("You can’t use this menu.", ephemeral=True)
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("You can’t use this menu.", ephemeral=True)
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.update_message(interaction)


class Servers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_owner(self, user_id: int) -> bool:
        return user_id in BOT_OWNER_IDS

    async def generate_pages(self, guilds):
        """Split guild list into multiple embed pages."""
        pages = []
        per_page = 10
        total_members = sum(g.member_count or 0 for g in guilds)

        for i in range(0, len(guilds), per_page):
            chunk = guilds[i:i + per_page]
            embed = discord.Embed(
                title=f"I'm currently in {len(guilds)} servers",
                description=f"Total users across all servers: **{total_members:,}**",
                color=discord.Color.blurple()
            )

            for guild in chunk:
                try:
                    channel = next(
                        (ch for ch in guild.text_channels if ch.permissions_for(guild.me).create_instant_invite),
                        None
                    )
                    if channel:
                        invite = await channel.create_invite(max_age=300, max_uses=1, reason="Bot owner request")
                        invite_link = invite.url
                    else:
                        invite_link = "No invite permission"
                except Exception:
                    invite_link = "Unable to create invite"

                member_count = guild.member_count or 0
                owner_name = guild.owner.name if guild.owner else "Unknown"
                value = (
                    f"Owner: **{owner_name}**\n"
                    f"Members: **{member_count:,}**\n"
                    f"Invite: {invite_link}"
                )
                embed.add_field(name=guild.name, value=value, inline=False)

            page_number = (i // per_page) + 1
            embed.set_footer(text=f"Page {page_number}/{(len(guilds) + per_page - 1) // per_page}")
            pages.append(embed)

        return pages

    @commands.command(name="servers", help="Show all servers the bot is in (Bot Owners only).")
    async def servers(self, ctx: commands.Context):
        if not self.is_owner(ctx.author.id):
            embed = discord.Embed(
                title="Permission Denied",
                description="Only bot owners can use this command.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        guilds = sorted(self.bot.guilds, key=lambda g: g.member_count or 0, reverse=True)
        pages = await self.generate_pages(guilds)

        try:
            view = ServerPaginator(pages, ctx.author)
            await ctx.author.send(embed=pages[0], view=view)
            msg = await ctx.reply("Check your DMs — I've sent the server list there!", mention_author=False)
            await msg.delete(delay=5)
        except discord.Forbidden:
            await ctx.reply("I couldn't DM you! Please enable DMs from server members.", mention_author=False)


async def setup(bot):
    await bot.add_cog(Servers(bot))