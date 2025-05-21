# Discord Order Command Bot

A Discord bot to streamline the ordering process in ZR Eats by parsing ticket embeds, consuming virtual cards and emails from a local SQLite pool, and formatting commands for multiple ordering bots (Fusion Assist, Fusion Order, and Wool Order).

## Features

- **Slash Commands**: `/fusion_assist`, `/fusion_order`, `/wool_order`
- **Embed Parsing**: Automatically extracts Group Cart Link, Name, Address Line 2, Delivery Notes, and Tip Amount from the ticket bot’s first embed.
- **Card & Email Pools**: Consumes cards and emails from an on-disk SQLite database (`data/pool.db`) and deletes used entries.
- **Field Validation**:
  - Skips `Name`, `Address Line 2`, and `Delivery Notes` if marked “N/A” or “None.”
  - Adds `override_dropoff:Leave at Door` if “leave” appears in Delivery Notes (Fusion commands only).
  - Normalizes names into “First Last” format, removing commas.
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

## Managing Card & Email Pools

Populate your pools via the Python script `add_to_pool.py`, or directly with the SQLite shell:

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

- **SQLite shell**:
  ```bash
  cd data
  sqlite3 pool.db
  INSERT INTO cards (number, cvv) VALUES ('1234567812345678', '212');
  INSERT INTO emails (email) VALUES ('example@gmail.com');
  .exit
  ```

## Running the Bot

```bash
python bot.py
```

Once the bot is online, use the slash commands in a ticket channel created by your ticket bot. All responses are ephemeral and visible only to the owner.

## Slash Command Usage

- **`/fusion_assist`**  
  Formats a Fusion “assist” command (no email).  
- **`/fusion_order`**  
  Formats a Fusion “order” command (includes email).  
- **`/wool_order`**  
  Formats a Wool order URL command.

Each command will return the properly formatted string plus a “Tip: $…” line.

## Troubleshooting

- **“Card pool is empty” or “Email pool is empty”**:  
  Populate your pools as described above.
- **Missing embed error**:  
  Ensure the ticket bot’s first message in the channel contains at least two embeds.
- **Permission denied**:  
  Verify your `OWNER_ID` in `.env` matches your Discord user ID.

## Contributing

Feel free to open issues or pull requests for enhancements!
