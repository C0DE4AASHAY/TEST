import os
import json
import discord
import asyncio
import logging
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands, tasks

# ----------------- Load .env -----------------

load_dotenv()

# ----------------- Logging Setup -----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ----------------- Constants -----------------

PREFIX_FILE = "Data/prefixes.json"
DEFAULT_PREFIX = "-"

# ----------------- Prefix Handling -----------------

def load_prefixes():
    if not os.path.exists(PREFIX_FILE):
        os.makedirs(os.path.dirname(PREFIX_FILE), exist_ok=True)
        return {}
    with open(PREFIX_FILE, "r") as f:
        return json.load(f)

def get_prefix(bot, message):
    if not message.guild:
        return DEFAULT_PREFIX
    prefixes = load_prefixes()
    guild_id = str(message.guild.id)
    custom = prefixes.get(guild_id, [])
    return commands.when_mentioned_or(DEFAULT_PREFIX, *custom)(bot, message)

# ----------------- Intents -----------------

intents = discord.Intents.all()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True


# ----------------- Bot Setup -----------------

bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    help_command=None
)

# ----------------- Presence Loop -----------------
@tasks.loop(seconds=10)
async def update_presence():
    members = sum((g.member_count or 0) for g in bot.guilds)
    activities = [
        discord.Activity(type=discord.ActivityType.listening, name="/help"),
        discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servers | {members} members")
    ]
    for activity in activities:
        await bot.change_presence(activity=activity)
        await asyncio.sleep(5)

# ----------------- On Ready -----------------

@bot.event
async def on_ready():
    logging.info(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    logging.info(f"✅ Connected to {len(bot.guilds)} servers")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logging.info(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        logging.error(f"❌ Failed to sync slash commands: {e}")

    if not update_presence.is_running():
        update_presence.start()

# ----------------- Load Cogs -----------------

async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('_'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logging.info(f"✅ Loaded: {filename}")
            except Exception as e:
                logging.error(f"❌ Failed to load {filename}: {e}")

# ----------------- Run Bot -----------------

async def main():
    async with bot:
        await load_extensions()
        token = os.getenv("TOKEN")
        if not token:
            logging.error("❌ Bot token not found in environment!")
            return
        await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Bot manually stopped.")
    except Exception as e:
        logging.error(f"❗ Fatal Error: {e}")
