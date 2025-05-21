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
        ('5187258137251227', '525'),
        ('5443178313028845', '375'),
        ('5443176851326084', '625'),
        ('5443178089601890', '460'),
        ('5443178448988962', '130'),
    ]
    emails_to_add = [
    'kirsten.cervantes1630@prin.cloud',
    'kristin.cannon3182@grabmezrfoods.store',
    'krystal.anderson0894@goodprineats.info',
    'lauren.park3653@grabmezrfoods.store',
    'linda.sheppard6356@grabmezrfoods.store',
    'lindsay.long2071@shopgoodeatstech.online',
    'lisa.hayes1595@grabmezrfoods.store',
    'luke.grant6457@grabmezrfoods.store',
    'michael.hall4419@grabmezrfoods.store',
    'michael.romero8850@grabmezrfoods.store',
    'michael.williams0613@grabmezrfoods.store',
    'paul.moore7041@grabmezrfoods.store',
    'peter.mcintosh5984@prin.cloud',
    'raymond.miller3436@prin.cloud',
    'rebecca.williams3292@richardplainjanemail.info',
    'reginald.sanders6970@goodprineats.info',
    'richard.meza5887@grabmezrfoods.store',
    'robert.hernandez4976@grabmezrfoods.store',
    'ronald.jones1499@grabmezrfoods.store',
    'ronald.tran8726@richardplainjanemail.info',
    'russell.wallace5014@goodprineats.info',
    'samantha.miller4717@prin.cloud',
    'samuel.reed2365@prin.cloud',
    'sarah.keller2108@goodprineats.info',
    'sean.white3262@prin.cloud',
    'stacey.hernandez0240@grabmezrfoods.store',
    'stephanie.rodriguez6306@richardplainjanemail.info',
    'steve.harris6916@grabmezrfoods.store',
    'susan.bernard4571@goodprineats.info',
    'taylor.mays0102@grabmezrfoods.store',
    'teresa.holland4563@grabmezrfoods.store',
    'terri.marshall5707@richardplainjanemail.info',
    'timothy.arnold7474@richardplainjanemail.info',
    'todd.rodriguez1401@prin.cloud',
    'tracy.brown5800@grabmezrfoods.store',
    'travis.manning4196@prin.cloud',
    'walter.baird9534@grabmezrfoods.store',
    'wayne.tyler9724@richardplainjanemail.info',
    ]

    add_cards(cards_to_add)
    add_emails(emails_to_add)
    print("Done inserting cards and emails!")