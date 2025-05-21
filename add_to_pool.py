import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'data' / 'pool.db'

def add_cards(cards):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executemany(
        'INSERT INTO cards (number, cvv) VALUES (?, ?)',
        cards
    )
    conn.commit()
    conn.close()

def add_emails(emails):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executemany(
        'INSERT INTO emails (email) VALUES (?)',
        [(e,) for e in emails]
    )
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # Example data—replace these lists with your real values.
    cards_to_add = [
        ('1234567812345678', '212'),
        ('8765432187654321', '123'),
    ]
    emails_to_add = [
        'example@gmail.com',
        'foo@bar.com',
    ]

    add_cards(cards_to_add)
    add_emails(emails_to_add)
    print("Done inserting cards and emails!")