import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import LayoutView, Container, Separator, TextDisplay
import aiohttp
import ssl
import socket
from datetime import datetime, timezone


class Whois(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.bootstrap_cache = None

    async def cog_unload(self):
        await self.session.close()

    async def fetch_json(self, url):
        try:
            async with self.session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
        except:
            return None

    async def get_bootstrap(self):
        if self.bootstrap_cache:
            return self.bootstrap_cache

        data = await self.fetch_json("https://data.iana.org/rdap/dns.json")
        if data:
            self.bootstrap_cache = data
        return data

    async def fetch_rdap(self, domain):
        tld = domain.split(".")[-1]
        bootstrap = await self.get_bootstrap()
        if not bootstrap:
            return None

        rdap_url = None
        for entry in bootstrap.get("services", []):
            if tld in entry[0]:
                rdap_url = entry[1][0]
                break

        if not rdap_url:
            return None

        return await self.fetch_json(f"{rdap_url}domain/{domain}")

    def parse_date(self, value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except:
            return None

    def calculate_age_days(self, created):
        if not created:
            return None
        now = datetime.now(timezone.utc)
        return (now - created).days

    async def get_ssl_info(self, domain):
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()

            issuer = dict(x[0] for x in cert["issuer"]).get("organizationName", "Unknown")
            expiry_raw = cert["notAfter"]
            expiry = datetime.strptime(expiry_raw, "%b %d %H:%M:%S %Y %Z")
            days_left = (expiry - datetime.utcnow()).days

            return issuer, expiry.strftime("%d/%m/%Y"), days_left
        except:
            return None, None, None

    async def resolve_ip(self, domain):
        try:
            return socket.gethostbyname(domain)
        except:
            return None

    @app_commands.command(name="whois", description="Advanced domain lookup")
    async def whois(self, interaction: discord.Interaction, domain: str):
        await interaction.response.defer(thinking=True)

        try:
            domain = domain.lower().strip()
            if domain.startswith("http"):
                domain = domain.split("//")[-1].split("/")[0]

            data = await self.fetch_rdap(domain)
            if not data:
                return await interaction.followup.send(
                    "Domain not found or RDAP not supported."
                )

            registrar = "Unknown"
            created_dt = None
            expiry_dt = None

            for entity in data.get("entities", []):
                if "registrar" in entity.get("roles", []):
                    vcard = entity.get("vcardArray", [])
                    if isinstance(vcard, list) and len(vcard) > 1:
                        for item in vcard[1]:
                            if item[0] == "fn":
                                registrar = item[3]
                                break

            for event in data.get("events", []):
                if event.get("eventAction") == "registration":
                    created_dt = self.parse_date(event.get("eventDate"))
                elif event.get("eventAction") == "expiration":
                    expiry_dt = self.parse_date(event.get("eventDate"))

            age_days = self.calculate_age_days(created_dt)

            ssl_issuer, ssl_expiry, ssl_days = await self.get_ssl_info(domain)
            ip_address = await self.resolve_ip(domain)

            view = LayoutView()
            container = Container()

            container.add_item(TextDisplay(f"## WHOIS â€” {domain}"))
            container.add_item(Separator())

            container.add_item(TextDisplay(
                f"**Registrar:** {registrar}\n"
                f"**Created:** {created_dt.strftime('%d/%m/%Y') if created_dt else 'Unknown'}\n"
                f"**Expires:** {expiry_dt.strftime('%d/%m/%Y') if expiry_dt else 'Unknown'}"
            ))

            container.add_item(Separator())

            container.add_item(TextDisplay(
                f"**Domain Age:** {age_days} days" if age_days else "**Domain Age:** Unknown"
            ))

            if age_days is not None and age_days < 30:
                container.add_item(TextDisplay("âš  New domain (less than 30 days old)"))

            container.add_item(Separator())

            if ssl_issuer:
                container.add_item(TextDisplay(
                    f"**SSL Issuer:** {ssl_issuer}\n"
                    f"**SSL Expires:** {ssl_expiry}\n"
                    f"**Days Left:** {ssl_days}"
                ))

                container.add_item(Separator())

            container.add_item(TextDisplay(
                f"**IP Address:** {ip_address or 'Unknown'}"
            ))

            view.add_item(container)

            await interaction.followup.send(view=view)

        except Exception as e:
            print("WHOIS Error:", e)
            await interaction.followup.send("Something went wrong.")


async def setup(bot):
    await bot.add_cog(Whois(bot))