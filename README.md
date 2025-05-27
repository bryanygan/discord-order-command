# Discord Order Command Bot

A Discord bot to streamline the ordering process in ZR Eats by parsing ticket embeds, consuming virtual cards and emails from a local SQLite pool, and formatting commands for multiple ordering bots (Fusion Assist, Fusion Order, and Wool Order).

## Features

- **Slash Commands**: `/fusion_assist`, `/fusion_order`, `/wool_order`
- **Admin Commands**: `/add_card`, `/add_email`, `/bulk_cards`, `/read_cards`, `/read_emails`, `/remove_card`, `/remove_email`
- **Logging Commands**: `/print_logs`, `/log_stats`
- **Embed Parsing**: Automatically extracts Group Cart Link, Name, Address Line 2, Delivery Notes, and Tip Amount from the ticket bot's first embed.
- **Card & Email Pools**: Consumes cards and emails from an on-disk SQLite database (`data/pool.db`) and deletes used entries.
- **Comprehensive Logging**: All command outputs are automatically logged to JSON, CSV, and TXT files with timestamps and tracking data.
- **Field Validation**:
  - Skips `Name`, `Address Line 2`, and `Delivery Notes` if marked "N/A" or "None."
  - Adds `override_dropoff:Leave at Door` if "leave" appears in Delivery Notes (Fusion commands only).
  - Normalizes names into "First Last" format, removing commas.
- **Permissions**: Only the configured `OWNER_ID` can invoke commands, with ephemeral responses.
- **Easy Setup**: Zero-config SQLite, environment variables via `.env`, and runs on Python 3.10+.

## Prerequisites

- Python 3.10 or higher
- `pip` for package management

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/bryanygan/discord-order-command.git
   cd discord-order-command
   ```

2. **Create a virtual environment** (optional, but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Environment variables**: Create a `.env` file in the project root:

   ```dotenv
   BOT_TOKEN=your_bot_token_here
   OWNER_ID=123456776543219130
   ```

2. **Database initialization**: On first run, `db.py` will auto-create `data/pool.db` with `cards` and `emails` tables.

3. **Logging setup**: The bot automatically creates a `logs/` directory and saves all command outputs in multiple formats.

## Managing Card & Email Pools

You can populate your pools using several methods:

### Using Slash Commands (Recommended)

- **Single entries**:
  - `/add_card number:1234567812345678 cvv:123` - Add a single card
  - `/add_email email:example@gmail.com` - Add a single email
  - `/add_email email:priority@gmail.com top:True` - Add an email to be used first

- **Bulk card upload**:
  - `/bulk_cards` - Upload a `.txt` file with cards (format: `cardnum,cvv` per line)

- **View current pools**:
  - `/read_cards` - List all cards in the pool
  - `/read_emails` - List all emails in the pool

- **Remove entries**:
  - `/remove_card number:1234567812345678 cvv:123` - Remove a specific card
  - `/remove_email email:example@gmail.com` - Remove a specific email

### Using Python Script

- **Python script**:
  ```python
  from add_to_pool import add_cards, add_emails

  cards = [
      ('1234567812345678', '212'),
      ('8765432187654321', '123'),
  ]
  emails = [
      'example@gmail.com',
      'foo@bar.com',
  ]

  add_cards(cards)
  add_emails(emails)
  ```

### Using SQLite Shell

- **SQLite shell**:
  ```bash
  cd data
  sqlite3 pool.db
  INSERT INTO cards (number, cvv) VALUES ('1234567812345678', '212');
  INSERT INTO emails (email) VALUES ('example@gmail.com');
  .exit
  ```

### Bulk Card File Format

For the `/bulk_cards` command, create a text file with one card per line:
```
1234567812345678,123
9876543210987654,456
5555444433332222,789
```

## Running the Bot

```bash
python bot.py
```

Once the bot is online, use the slash commands in a ticket channel created by your ticket bot. All responses are ephemeral and visible only to the owner.

## Slash Command Usage

### Order Commands
- **`/fusion_assist`**  
  Formats a Fusion "assist" command. Choose between Postmates or UberEats mode.
  - Optional `email` parameter: Add a custom email to the command output
  - Example: `/fusion_assist mode:UberEats email:custom@example.com`
  
- **`/fusion_order`**  
  Formats a Fusion "order" command (includes email from pool). No mode selection required.
  
- **`/wool_order`**  
  Formats a Wool order URL command.

Each command will return the properly formatted string plus a "Tip: $…" line.

### Logging Commands (Owner Only)
- **`/print_logs`** - Display recent command logs with email and card digits 9-16
  - Parameter: `count` (default: 10, max: 100)
  - Output format: `email@example.com | 1567-4013`
  - Long outputs are automatically sent as `.txt` file attachments
  
- **`/log_stats`** - View command statistics and usage data
  - Optional parameter: `month` in YYYYMM format (e.g., 202405)
  - Shows total commands, unique emails/cards used, command breakdowns

### Admin Commands (Owner Only)
- **`/add_card`** - Add a single card to the pool
- **`/add_email`** - Add a single email to the pool (with optional priority)
- **`/bulk_cards`** - Upload a text file with multiple cards
- **`/read_cards`** - View all cards currently in the pool
- **`/read_emails`** - View all emails currently in the pool
- **`/remove_card`** - Remove a specific card from the pool
- **`/remove_email`** - Remove a specific email from the pool

## Logging System

The bot automatically logs all command outputs to multiple file formats:

### Log File Types
- **JSON files** (`logs/commands_YYYYMM.json`) - Structured data for programmatic access
- **CSV files** (`logs/commands_YYYYMM.csv`) - Easy analysis in Excel/Google Sheets
- **TXT files** (`logs/commands_YYYYMMDD.txt`) - Human-readable daily logs

### Logged Information
- Timestamp of command execution
- Command type (fusion_assist, fusion_order, wool_order)
- Complete command output
- Email used (from pool or custom)
- Full card information with CVV
- Card digits 9-12 and 9-16 for tracking
- Additional metadata

### Log Management
- Monthly rotation for JSON/CSV files
- Daily rotation for TXT files
- Automatic directory creation
- Error handling and validation

## File Structure

```
discord-order-command/
├── bot.py              # Main bot file
├── db.py               # Database management
├── logging_utils.py    # Logging functionality
├── add_to_pool.py      # Helper script for adding cards/emails
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── .env               # Environment variables (create this)
├── data/
│   └── pool.db        # SQLite database (auto-created)
└── logs/              # Log files (auto-created)
    ├── commands_202405.json
    ├── commands_202405.csv
    └── commands_20240515.txt
```

## Troubleshooting

- **"Card pool is empty" or "Email pool is empty"**:  
  Populate your pools using the admin commands or methods described above.
  
- **Missing embed error**:  
  Ensure the ticket bot's first message in the channel contains at least two embeds.
  
- **Permission denied**:  
  Verify your `OWNER_ID` in `.env` matches your Discord user ID.
  
- **Bulk upload errors**:  
  Ensure your text file uses the correct format (`cardnum,cvv`) and contains valid card data.
  
- **Logging errors**:  
  Check that the bot has write permissions in the project directory. The `logs/` folder will be created automatically.
  
- **Missing log files**:  
  Log files are created when the first command is executed. Use `/log_stats` to verify logging is working.

## Security Notes

- All responses are ephemeral (only visible to the command user)
- Card numbers are logged in full for operational needs - ensure log files are secured
- Only the configured `OWNER_ID` can execute any commands
- Database and log files should be backed up and secured appropriately

## Contributing

Feel free to open issues or pull requests for enhancements!