import discord
from discord.ext import commands
import asyncio
import datetime
import os

# === SECURE TOKEN PULL ===
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("SET DISCORD_TOKEN ENV VAR! For local test: TOKEN = 'your_token_here'")
# ===========================================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

def fmt(ts): 
    return ts.strftime("%Y-%m-%d %H:%M:%S")

@bot.event
async def on_ready():
    print(f'[SECURE BOT LIVE] {bot.user} | Token safe, ready to scrape')

@bot.command(name='scrape')
@commands.has_permissions(administrator=True)
async def scrape(ctx):
    if not ctx.guild:
        return await ctx.send("Server only, asshole.")

    await ctx.send("**SECURE SCRAPE MODE ACTIVATED** 🔥 No leaks, no resets.")

    guild = ctx.guild
    dump_file = f"{guild.name.replace(' ', '_')}_SECURE_DUMP.txt"

    with open(dump_file, 'w', encoding='utf-8') as f:
        f.write(f"SERVER: {guild.name} ({guild.id})\n")
        f.write(f"SCRAPED BY: {ctx.author}\n")
        f.write(f"TIME: {fmt(datetime.datetime.now())}\n")
        f.write("="*60 + "\n\n")

    total = 0
    for channel in guild.text_channels:
        if not channel.permissions_for(guild.me).read_message_history:
            continue

        msg_count = 0
        try:
            async for msg in channel.history(limit=None, oldest_first=True):
                if msg.author.bot:
                    continue

                user = f"{msg.author.display_name}"
                if msg.author.discriminator != '0':
                    user += f"#{msg.author.discriminator}"

                content = msg.clean_content.replace('\n', ' ').strip()
                if not content:
                    continue

                with open(dump_file, 'a', encoding='utf-8') as f:
                    f.write(f"user: {user}\n")
                    f.write(f"message: {content}\n")
                    f.write(f"channel: #{channel.name}\n")
                    f.write(f"time: {fmt(msg.created_at)}\n")
                    f.write("-" * 40 + "\n")

                msg_count += 1
                total += 1

                # Anti-rate-limit (prevents auto-reset)
                if total % 50 == 0:
                    await asyncio.sleep(1)

            await ctx.send(f"✅ `{msg_count}` messages from `#{channel.name}`")

        except Exception as e:
            await ctx.send(f"⚠️ Fuckup in `#{channel.name}`: {e}")

    # SEND TO DM
    try:
        with open(dump_file, 'rb') as f:
            await ctx.author.send(
                f"**SECURE DUMP COMPLETE**\n"
                f"Server: `{guild.name}`\n"
                f"Total Messages: `{total}`\n"
                f"Token-proof attached:",
                file=discord.File(f, dump_file)
            )
        await ctx.send(f"**DUMP IN YOUR DMs** 📥\nTotal: `{total}` messages. Token safe.")
    except Exception as e:
        await ctx.send(f"DM failed: {e}\nGrab file from host: `{dump_file}`")

    # Clean up
    try:
        os.remove(dump_file)
    except:
        pass

bot.run(TOKEN)
