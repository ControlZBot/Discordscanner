import discord
from discord.ext import commands
import asyncio
import datetime
import os

# === TOKEN FROM RENDER ENV (SECURE, NO LEAKS) ===
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    print("FATAL: DISCORD_TOKEN NOT SET IN RENDER ENV!")
    exit(1)
# ================================================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# === PING TEST COMMAND ===
@bot.command(name='ping')
async def ping(ctx):
    await ctx.send(f"**PONG!** Latency: `{round(bot.latency * 1000)}ms` | Bot is **LIVE**")

# === FULL SERVER SCRAPE COMMAND ===
@bot.command(name='scrape')
@commands.has_permissions(administrator=True)
async def scrape(ctx):
    if not ctx.guild:
        return await ctx.send("❌ **Server-only command.**")

    await ctx.send("🚀 **FULL SERVER SCRAPE STARTED** — This may take several minutes...")

    guild = ctx.guild
    dump_file = f"{guild.name.replace(' ', '_')}_FULL_DUMP.txt"

    # Header
    with open(dump_file, 'w', encoding='utf-8') as f:
        f.write(f"SERVER: {guild.name} ({guild.id})\n")
        f.write(f"SCRAPED BY: {ctx.author}\n")
        f.write(f"TIME: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")

    total_messages = 0

    for channel in guild.text_channels:
        if not channel.permissions_for(guild.me).read_message_history:
            await ctx.send(f"⚠️ **No access** to `#{channel.name}`")
            continue

        msg_count = 0
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                if message.author.bot:
                    continue  # Skip bots

                user = f"{message.author.display_name}"
                if message.author.discriminator != '0':
                    user += f"#{message.author.discriminator}"

                content = message.clean_content.replace('\n', ' ').strip()
                if not content:
                    continue

                timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")

                with open(dump_file, 'a', encoding='utf-8') as f:
                    f.write(f"user: {user}\n")
                    f.write(f"message: {content}\n")
                    f.write(f"channel: #{channel.name}\n")
                    f.write(f"time: {timestamp}\n")
                    f.write("-" * 40 + "\n")

                msg_count += 1
                total_messages += 1

                # Avoid rate limits
                if total_messages % 100 == 0:
                    await asyncio.sleep(0.5)

            await ctx.send(f"✅ **Scraped** `#{channel.name}` — `{msg_count}` messages")

        except Exception as e:
            await ctx.send(f"❌ **Error** in `#{channel.name}`: `{e}`")

    # === SEND FILE TO DM ===
    try:
        with open(dump_file, 'rb') as f:
            await ctx.author.send(
                f"**FULL SERVER DUMP COMPLETE** 📁\n"
                f"**Server:** `{guild.name}`\n"
                f"**Total Messages:** `{total_messages}`\n"
                f"**File:** `{dump_file}`",
                file=discord.File(f, dump_file)
            )
        await ctx.send(f"✅ **DUMP SENT TO YOUR DMs!** Total: `{total_messages}` messages.")
    except Exception as e:
        await ctx.send(f"❌ **DM failed:** `{e}`\nFile saved on server: `{dump_file}`")

    # === CLEAN UP ===
    try:
        os.remove(dump_file)
    except:
        pass

# === BOT READY ===
@bot.event
async def on_ready():
    print(f"[BOT ONLINE] {bot.user} | Connected to {len(bot.guilds)} server(s)")

# === RUN ===
bot.run(TOKEN)
