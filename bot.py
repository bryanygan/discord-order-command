import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import sqlite3
from db import get_and_remove_card, get_and_remove_email, DB_PATH
from logging_utils import log_command_output, get_log_stats  # Import our logging functions

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
    # Replace commas with spaces, collapse and strip whitespace
    cleaned = name.replace(",", " ").strip()    
    parts = cleaned.split()
    if len(parts) >= 2:
        first = parts[0].strip().title()
        last = parts[1].strip().title()
        return f"{first} {last}"
    if len(parts) == 1:
        w = parts[0].strip().title()
        return f"{w} {w[0].upper()}"
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
@app_commands.choices(mode=[
    app_commands.Choice(name='Postmates', value='p'),
    app_commands.Choice(name='UberEats', value='u'),
])
@app_commands.describe(email="Optional: Add a custom email to the end of the command")
async def fusion_assist(interaction: discord.Interaction, mode: app_commands.Choice[str], email: str = None):
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
    
    # Build base command with card details and optional email
    base_command = f"{info['link']},{number},{EXP_MONTH},{EXP_YEAR},{cvv},{ZIP_CODE}"
    if email:
        base_command += f",{email}"
    
    parts = [f"/assist order order_details:{base_command}"]
    
    if mode.value == 'p':
        parts.append('mode:postmates')
    elif mode.value == 'u':
        parts.append('mode:ubereats')
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

    # LOG THE COMMAND OUTPUT
    log_command_output(
        command_type="fusion_assist",
        user_id=interaction.user.id,
        username=str(interaction.user),
        channel_id=interaction.channel.id,
        guild_id=interaction.guild.id if interaction.guild else None,
        command_output=command,
        tip_amount=info['tip'],
        card_used=card,
        email_used=email,  # Log the custom email if provided
        additional_data={"mode": mode.value, "parsed_fields": info, "custom_email": email}
    )

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

    # LOG THE COMMAND OUTPUT
    log_command_output(
        command_type="fusion_order",
        user_id=interaction.user.id,
        username=str(interaction.user),
        channel_id=interaction.channel.id,
        guild_id=interaction.guild.id if interaction.guild else None,
        command_output=command,
        tip_amount=info['tip'],
        card_used=card,
        email_used=email,
        additional_data={"parsed_fields": info}
    )

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

    # LOG THE COMMAND OUTPUT
    log_command_output(
        command_type="wool_order",
        user_id=interaction.user.id,
        username=str(interaction.user),
        channel_id=interaction.channel.id,
        guild_id=interaction.guild.id if interaction.guild else None,
        command_output=command,
        tip_amount=info['tip'],
        card_used=card,
        email_used=email,
        additional_data={"parsed_fields": info}
    )

    await interaction.response.send_message(f"```{command}```\n{tip_line}", ephemeral=True)

# Print recent logs
@bot.tree.command(name='print_logs', description='(Admin) Print recent command logs with email and card digits 9-16')
@app_commands.describe(count="Number of recent logs to retrieve (default: 10, max: 100)")
async def print_logs(interaction: discord.Interaction, count: int = 10):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)
    
    # Validate count
    if count < 1:
        return await interaction.response.send_message("❌ Count must be at least 1.", ephemeral=True)
    if count > 100:
        return await interaction.response.send_message("❌ Maximum count is 100.", ephemeral=True)
    
    # Import the function from logging_utils
    from logging_utils import get_recent_logs
    
    logs = get_recent_logs(count)
    
    if not logs:
        return await interaction.response.send_message("❌ No logs found.", ephemeral=True)
    
    # Format the output
    output_lines = []
    for log in logs:
        email = log.get('email_used', 'N/A')
        
        # Format digits 9-16 with hyphens every 4 digits
        digits_9_16 = log.get('card_digits_9_16')
        if digits_9_16 and len(digits_9_16) == 8:
            # Split into groups of 4 and join with hyphens
            formatted_digits = f"{digits_9_16[:4]}-{digits_9_16[4:]}"
        else:
            formatted_digits = "N/A"
        
        output_lines.append(f"{email} | {formatted_digits}")
    
    output_text = "\n".join(output_lines)
    
    # Check if output is too long for Discord message (2000 char limit)
    if len(output_text) > 1800:  # Leave some buffer for formatting
        # Create a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(f"Recent {len(logs)} Command Logs\n")
            f.write("=" * 40 + "\n\n")
            f.write("Email | Card Digits 9-16\n")
            f.write("-" * 40 + "\n")
            f.write(output_text)
            temp_file_path = f.name
        
        try:
            # Send as file attachment
            with open(temp_file_path, 'rb') as f:
                discord_file = discord.File(f, filename=f"recent_logs_{count}.txt")
                await interaction.response.send_message(
                    f"📄 **Recent {len(logs)} Command Logs** (sent as file due to length)",
                    file=discord_file,
                    ephemeral=True
                )
        finally:
            # Clean up temp file
            import os
            try:
                os.unlink(temp_file_path)
            except:
                pass
    else:
        # Send as regular message
        formatted_output = f"📋 **Recent {len(logs)} Command Logs**\n```\nEmail | Card Digits 9-16\n{'-' * 40}\n{output_text}\n```"
        await interaction.response.send_message(formatted_output, ephemeral=True)

# View log statistics
@bot.tree.command(name='log_stats', description='(Admin) View command logging statistics')
@app_commands.describe(month="Month in YYYYMM format (e.g., 202405). Leave blank for current month.")
async def log_stats(interaction: discord.Interaction, month: str = None):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)
    
    stats = get_log_stats(month)
    
    if "error" in stats:
        return await interaction.response.send_message(f"❌ {stats['error']}", ephemeral=True)
    
    # Format the statistics
    stats_text = f"""📊 **Command Statistics for {month or 'Current Month'}**

**Total Commands:** {stats['total_commands']}
**Unique Emails Used:** {stats['unique_emails']}
**Unique Cards Used:** {stats['unique_cards']}

**Commands by Type:**"""
    
    for cmd_type, count in stats['command_types'].items():
        stats_text += f"\n  • {cmd_type}: {count}"
    
    stats_text += f"\n\n**Emails Used:** {', '.join(stats['emails_used'])}"
    stats_text += f"\n**Card Digits 9-12 Used:** {', '.join(stats['cards_used'])}"
    
    if stats['date_range']['start']:
        stats_text += f"\n**Date Range:** {stats['date_range']['start'][:10]} to {stats['date_range']['end'][:10]}"
    
    await interaction.response.send_message(stats_text, ephemeral=True)

# All your existing admin commands remain the same...
@bot.tree.command(name='add_card', description='(Admin) Add a card to the pool')
async def add_card(interaction: discord.Interaction, number: str, cvv: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO cards (number, cvv) VALUES (?, ?)", (number, cvv))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"✅ Card ending in {number[-4:]} added.", ephemeral=True)

@bot.tree.command(name='add_email', description='(Admin) Add an email to the pool')
@app_commands.describe(top="Add this email to the top of the pool so it's used first")
async def add_email(interaction: discord.Interaction, email: str, top: bool = False):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if top:
        cur.execute("SELECT MIN(id) FROM emails")
        row = cur.fetchone()
        min_id = row[0] if row and row[0] is not None else None
        if min_id is None:
            # No existing emails, just insert normally
            cur.execute("INSERT INTO emails (email) VALUES (?)", (email,))
        else:
            # Prepend by assigning a lower id than any existing
            new_id = min_id - 1
            cur.execute("INSERT INTO emails (id, email) VALUES (?, ?)", (new_id, email))
    else:
        cur.execute("INSERT INTO emails (email) VALUES (?)", (email,))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"✅ Email `{email}` added.", ephemeral=True)

@bot.tree.command(name='bulk_cards', description='(Admin) Add multiple cards from a text file')
async def bulk_cards(interaction: discord.Interaction, file: discord.Attachment):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)
    
    # Check if the file is a text file
    if not file.filename.endswith('.txt'):
        return await interaction.response.send_message("❌ Please upload a .txt file.", ephemeral=True)
    
    # Check file size (limit to 1MB for safety)
    if file.size > 1024 * 1024:  # 1MB
        return await interaction.response.send_message("❌ File too large. Maximum size is 1MB.", ephemeral=True)
    
    try:
        # Download and read the file content
        file_content = await file.read()
        text_content = file_content.decode('utf-8')
        
        # Parse the lines
        lines = text_content.strip().split('\n')
        cards_to_add = []
        invalid_lines = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:  # Skip empty lines
                continue
                
            # Split by comma
            parts = line.split(',')
            if len(parts) != 2:
                invalid_lines.append(f"Line {i}: '{line}' (expected format: cardnum,cvv)")
                continue
            
            number, cvv = parts[0].strip(), parts[1].strip()
            
            # Basic validation
            if not number or not cvv:
                invalid_lines.append(f"Line {i}: '{line}' (empty card number or CVV)")
                continue
            
            # Check if card number is numeric and reasonable length
            if not number.isdigit() or len(number) < 13 or len(number) > 19:
                invalid_lines.append(f"Line {i}: '{line}' (invalid card number format)")
                continue
            
            # Check if CVV is numeric and reasonable length
            if not cvv.isdigit() or len(cvv) < 3 or len(cvv) > 4:
                invalid_lines.append(f"Line {i}: '{line}' (invalid CVV format)")
                continue
            
            cards_to_add.append((number, cvv))
        
        # If there are invalid lines, show them
        if invalid_lines:
            error_msg = "❌ Found invalid lines:\n" + "\n".join(invalid_lines[:10])  # Limit to first 10 errors
            if len(invalid_lines) > 10:
                error_msg += f"\n... and {len(invalid_lines) - 10} more errors"
            return await interaction.response.send_message(error_msg, ephemeral=True)
        
        # If no valid cards found
        if not cards_to_add:
            return await interaction.response.send_message("❌ No valid cards found in the file.", ephemeral=True)
        
        # Add cards to database
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        added_count = 0
        for number, cvv in cards_to_add:
            try:
                cur.execute("INSERT INTO cards (number, cvv) VALUES (?, ?)", (number, cvv))
                added_count += 1
            except sqlite3.IntegrityError:
                # Skip duplicate cards if there's a unique constraint
                continue
        
        conn.commit()
        conn.close()
        
        await interaction.response.send_message(
            f"✅ Successfully added {added_count} cards to the pool.", 
            ephemeral=True
        )
        
    except UnicodeDecodeError:
        await interaction.response.send_message("❌ Could not read file. Please ensure it's a valid UTF-8 text file.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error processing file: {str(e)}", ephemeral=True)

@bot.tree.command(name='read_cards', description='(Admin) List all cards in the pool')
async def read_cards(interaction: discord.Interaction):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT number, cvv FROM cards")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return await interaction.response.send_message("✅ No cards in the pool.", ephemeral=True)

    # format as cardnum,cvv per line
    lines = [f"{num},{cvv}" for num, cvv in rows]
    payload = "Cards in pool:\n" + "\n".join(lines)
    await interaction.response.send_message(f"```{payload}```", ephemeral=True)

@bot.tree.command(name='read_emails', description='(Admin) List all emails in the pool')
async def read_emails(interaction: discord.Interaction):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT email FROM emails")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return await interaction.response.send_message("✅ No emails in the pool.", ephemeral=True)

    lines = [email for (email,) in rows]
    payload = "Emails in pool:\n" + "\n".join(lines)
    await interaction.response.send_message(f"```{payload}```", ephemeral=True)

@bot.tree.command(name='remove_card', description='(Admin) Remove a card from the pool')
async def remove_card(interaction: discord.Interaction, number: str, cvv: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM cards WHERE number = ? AND cvv = ?", (number, cvv))
    deleted = cur.rowcount
    conn.commit()
    conn.close()

    if deleted:
        await interaction.response.send_message(
            f"✅ Removed card ending in {number[-4:]}.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ No matching card found in the pool.", ephemeral=True
        )

@bot.tree.command(name='remove_email', description='(Admin) Remove an email from the pool')
async def remove_email(interaction: discord.Interaction, email: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM emails WHERE email = ?", (email,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()

    if deleted:
        await interaction.response.send_message(
            f"✅ Removed email `{email}` from the pool.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ No matching email found in the pool.", ephemeral=True
        )

if __name__ == '__main__':
    bot.run(BOT_TOKEN)