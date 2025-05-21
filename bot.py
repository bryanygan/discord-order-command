import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from db import get_and_remove_card, get_and_remove_email

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID'))  # your Discord user ID

# Constants for card formatting
EXP_MONTH = '05'
EXP_YEAR = '30'
ZIP_CODE = '19104'

# Bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# Utility: fetch the first message's second embed in this channel
async def fetch_order_embed(channel: discord.TextChannel) -> discord.Embed:
    # Get the very first message in the channel
    msgs = [msg async for msg in channel.history(limit=1, oldest_first=True)]
    if not msgs or len(msgs[0].embeds) < 2:
        return None
    return msgs[0].embeds[1]

# Common embed parsing
def parse_fields(embed: discord.Embed) -> dict:
    data = {field.name: field.value for field in embed.fields}
    return {
        'link': data.get('Group Cart Link'),
        'name': data.get('Name', '').strip(),
        'addr2': data.get('Address Line 2', '').strip(),
        'notes': data.get('Delivery Notes', '').strip(),
        'tip': data.get('Tip Amount', '').strip()
    }

# Helper: normalize name into two words
def normalize_name(name: str) -> str:
    # Remove any commas used between first and last names
    cleaned = name.replace(",", "").strip()
    parts = cleaned.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    if len(parts) == 1:
        w = parts[0]
        return f"{w} {w[0]}"
    return ''

# Helper: check if a field value is valid (non-empty, not 'n/a' or 'none')
def is_valid_field(value: str) -> bool:
    """Return True if value is non-empty and not 'n/a' or 'none' (case-insensitive)."""
    return bool(value and value.strip().lower() not in ('n/a', 'none'))

# Slash command decorator
def owner_only(interaction: discord.Interaction) -> bool:
    return interaction.user.id == OWNER_ID

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# FusionAssist
@bot.tree.command(name='fusion_assist', description='Format a Fusion assist order')
async def fusion_assist(interaction: discord.Interaction):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ You are not authorized.", ephemeral=True)

    embed = await fetch_order_embed(interaction.channel)
    if embed is None:
        return await interaction.response.send_message(
            "❌ Could not find order embed.", ephemeral=True)

    info = parse_fields(embed)
    # get card
    card = get_and_remove_card()
    if card is None:
        return await interaction.response.send_message(
            "❌ Card pool is empty.", ephemeral=True)
    number, cvv = card

    raw_name = info['name']
    parts = [f"/assist order order_details:{info['link']},{number},{EXP_MONTH},{EXP_YEAR},{cvv},{ZIP_CODE}"]
    if is_valid_field(raw_name):
        name = normalize_name(raw_name)
        parts.append(f"override_name:{name}")
    if is_valid_field(info['addr2']):
        parts.append(f"override_aptorsuite:{info['addr2']}")
    notes = info['notes'].strip()
    if is_valid_field(notes):
        if notes.lower() == 'meet at door':
            parts.append("override_dropoff:Meet at Door")
        else:
            parts.append(f"override_notes:{notes}")
            if 'leave' in notes.lower():
                parts.append("override_dropoff:Leave at Door")

    command = ' '.join(parts)
    tip_line = f"Tip: ${info['tip']}"

    await interaction.response.send_message(f"```{command}```\n{tip_line}", ephemeral=True)

# FusionOrder
@bot.tree.command(name='fusion_order', description='Format a Fusion order with email')
async def fusion_order(interaction: discord.Interaction):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ You are not authorized.", ephemeral=True)

    embed = await fetch_order_embed(interaction.channel)
    if embed is None:
        return await interaction.response.send_message(
            "❌ Could not find order embed.", ephemeral=True)

    info = parse_fields(embed)
    # get card
    card = get_and_remove_card()
    if card is None:
        return await interaction.response.send_message(
            "❌ Card pool is empty.", ephemeral=True)
    number, cvv = card
    # get email
    email = get_and_remove_email()
    if email is None:
        return await interaction.response.send_message(
            "❌ Email pool is empty.", ephemeral=True)

    raw_name = info['name']
    parts = [f"/order uber order_details:{info['link']},{number},{EXP_MONTH},{EXP_YEAR},{cvv},{ZIP_CODE},{email}"]
    if is_valid_field(raw_name):
        name = normalize_name(raw_name)
        parts.append(f"override_name:{name}")
    if is_valid_field(info['addr2']):
        parts.append(f"override_aptorsuite:{info['addr2']}")
    notes = info['notes'].strip()
    if is_valid_field(notes):
        if notes.lower() == 'meet at door':
            parts.append("override_dropoff:Meet at Door")
        else:
            parts.append(f"override_notes:{notes}")
            if 'leave' in notes.lower():
                parts.append("override_dropoff:Leave at Door")

    command = ' '.join(parts)
    tip_line = f"Tip: ${info['tip']}"

    await interaction.response.send_message(f"```{command}```\n{tip_line}", ephemeral=True)

# WoolOrder
@bot.tree.command(name='wool_order', description='Format a Wool order')
async def wool_order(interaction: discord.Interaction):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ You are not authorized.", ephemeral=True)

    embed = await fetch_order_embed(interaction.channel)
    if embed is None:
        return await interaction.response.send_message(
            "❌ Could not find order embed.", ephemeral=True)

    info = parse_fields(embed)
    # get card
    card = get_and_remove_card()
    if card is None:
        return await interaction.response.send_message(
            "❌ Card pool is empty.", ephemeral=True)
    number, cvv = card
    # get email
    email = get_and_remove_email()
    if email is None:
        return await interaction.response.send_message(
            "❌ Email pool is empty.", ephemeral=True)

    # Format: link,number,MM/YY,cvv,zip,email
    parts = [f"{info['link']},{number},{EXP_MONTH}/{EXP_YEAR},{cvv},{ZIP_CODE},{email}"]
    command = parts[0]
    tip_line = f"Tip: ${info['tip']}"

    await interaction.response.send_message(f"```{command}```\n{tip_line}", ephemeral=True)

if __name__ == '__main__':
    bot.run(BOT_TOKEN)