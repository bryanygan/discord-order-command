import os
import json
import csv
from datetime import datetime
from typing import Dict, Any

# Create logs directory if it doesn't exist
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

def log_command_output(
    command_type: str,
    user_id: int,
    username: str,
    channel_id: int,
    guild_id: int,
    command_output: str,
    tip_amount: str = None,
    card_used: tuple = None,
    email_used: str = None,
    additional_data: Dict[str, Any] = None
):
    """
    Log command output to multiple formats (JSON, CSV, and TXT)
    
    Args:
        command_type: Type of command (fusion_assist, fusion_order, wool_order)
        user_id: Discord user ID
        username: Discord username
        channel_id: Discord channel ID
        guild_id: Discord guild ID
        command_output: The actual command string that was output
        tip_amount: Tip amount from the order
        card_used: Tuple of (card_number, cvv) that was consumed
        email_used: Email that was consumed
        additional_data: Any additional data to log
    """
    timestamp = datetime.now()
    
    # Prepare log entry
    log_entry = {
        "timestamp": timestamp.isoformat(),
        "command_type": command_type,
        "user_id": user_id,
        "username": username,
        "channel_id": channel_id,
        "guild_id": guild_id,
        "command_output": command_output,
        "tip_amount": tip_amount,
        "card_used": card_used[0][-4:] if card_used else None,  # Only log last 4 digits for security
        "card_cvv": card_used[1] if card_used else None,
        "email_used": email_used,
        "additional_data": additional_data or {}
    }
    
    # Log to JSON file (detailed structured data)
    json_file = os.path.join(LOGS_DIR, f"commands_{timestamp.strftime('%Y%m')}.json")
    _log_to_json(json_file, log_entry)
    
    # Log to CSV file (for easy analysis)
    csv_file = os.path.join(LOGS_DIR, f"commands_{timestamp.strftime('%Y%m')}.csv")
    _log_to_csv(csv_file, log_entry)
    
    # Log to daily text file (human readable)
    txt_file = os.path.join(LOGS_DIR, f"commands_{timestamp.strftime('%Y%m%d')}.txt")
    _log_to_txt(txt_file, log_entry, timestamp)

def _log_to_json(filename: str, log_entry: Dict[str, Any]):
    """Append log entry to JSON file"""
    try:
        # Read existing data
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = []
        
        # Append new entry
        data.append(log_entry)
        
        # Write back to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error logging to JSON: {e}")

def _log_to_csv(filename: str, log_entry: Dict[str, Any]):
    """Append log entry to CSV file"""
    try:
        # Define CSV headers
        headers = [
            "timestamp", "command_type", "user_id", "username", 
            "channel_id", "guild_id", "command_output", "tip_amount",
            "card_last4", "card_cvv", "email_used"
        ]
        
        # Check if file exists
        file_exists = os.path.exists(filename)
        
        # Prepare row data
        row_data = [
            log_entry["timestamp"],
            log_entry["command_type"],
            log_entry["user_id"],
            log_entry["username"],
            log_entry["channel_id"],
            log_entry["guild_id"],
            log_entry["command_output"],
            log_entry["tip_amount"],
            log_entry["card_used"],
            log_entry["card_cvv"],
            log_entry["email_used"]
        ]
        
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header if file is new
            if not file_exists:
                writer.writerow(headers)
            writer.writerow(row_data)
    except Exception as e:
        print(f"Error logging to CSV: {e}")

def _log_to_txt(filename: str, log_entry: Dict[str, Any], timestamp: datetime):
    """Append log entry to text file in human-readable format"""
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"TIMESTAMP: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"COMMAND TYPE: {log_entry['command_type']}\n")
            f.write(f"USER: {log_entry['username']} (ID: {log_entry['user_id']})\n")
            f.write(f"CHANNEL ID: {log_entry['channel_id']}\n")
            f.write(f"TIP AMOUNT: ${log_entry['tip_amount']}\n")
            if log_entry['card_used']:
                f.write(f"CARD USED: ****{log_entry['card_used']} (CVV: {log_entry['card_cvv']})\n")
            if log_entry['email_used']:
                f.write(f"EMAIL USED: {log_entry['email_used']}\n")
            f.write(f"\nCOMMAND OUTPUT:\n{log_entry['command_output']}\n")
            f.write(f"{'='*80}\n")
    except Exception as e:
        print(f"Error logging to TXT: {e}")

def get_log_stats(month: str = None) -> Dict[str, Any]:
    """
    Get statistics about logged commands
    
    Args:
        month: Optional month in YYYYMM format (e.g., "202405")
               If None, uses current month
    
    Returns:
        Dictionary with statistics
    """
    if month is None:
        month = datetime.now().strftime('%Y%m')
    
    json_file = os.path.join(LOGS_DIR, f"commands_{month}.json")
    
    if not os.path.exists(json_file):
        return {"error": "No log file found for specified month"}
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stats = {
            "total_commands": len(data),
            "command_types": {},
            "total_tips": 0,
            "users": set(),
            "date_range": {"start": None, "end": None}
        }
        
        for entry in data:
            # Count command types
            cmd_type = entry["command_type"]
            stats["command_types"][cmd_type] = stats["command_types"].get(cmd_type, 0) + 1
            
            # Sum tips
            if entry["tip_amount"]:
                try:
                    stats["total_tips"] += float(entry["tip_amount"])
                except ValueError:
                    pass
            
            # Track users
            stats["users"].add(entry["username"])
            
            # Track date range
            entry_date = entry["timestamp"]
            if stats["date_range"]["start"] is None or entry_date < stats["date_range"]["start"]:
                stats["date_range"]["start"] = entry_date
            if stats["date_range"]["end"] is None or entry_date > stats["date_range"]["end"]:
                stats["date_range"]["end"] = entry_date
        
        stats["unique_users"] = len(stats["users"])
        stats["users"] = list(stats["users"])  # Convert set to list for JSON serialization
        
        return stats
    except Exception as e:
        return {"error": f"Error reading log file: {e}"}