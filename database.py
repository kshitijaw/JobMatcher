# Shared DB used by app.py and worked.py

import sqlite3

DB = "jobs.db"

# Initiation of the DB
def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            email    TEXT NOT NULL,
            role     TEXT NOT NULL,
            city     TEXT NOT NULL,
            resume   TEXT NOT NULL,
            active   INTEGER DEFAULT 1,
            created  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_jobs (
            job_id      TEXT NOT NULL,
            subscriber  TEXT NOT NULL,
            seen_at     TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (job_id, subscriber)
        )
    """)
    conn.commit()
    conn.close()

# Everytime someone subscribes to the service this is called
def add_subscriber(email, role, city, resume):
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO subscribers (email, role, city, resume) VALUES (?,?,?,?)",
        (email, role, city, resume)
    )
    conn.commit()
    conn.close()

#Called every hour to get the subscriber
def get_subscribers():
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT email, role, city, resume FROM subscribers WHERE active=1"
    ).fetchall()
    conn.close()
    return [{"email": r[0], "role": r[1], "city": r[2], "resume": r[3]} for r in rows]

#Checking for duplicate jobs
def is_new_job(job_id, email):
    conn = sqlite3.connect(DB)
    row = conn.execute(
        "SELECT 1 FROM seen_jobs WHERE job_id=? AND subscriber=?", (job_id, email)
    ).fetchone()
    conn.close()
    return row is None

#Seen jobs data saved
def mark_seen(job_id, email):
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT OR IGNORE INTO seen_jobs (job_id, subscriber) VALUES (?,?)", (job_id, email)
    )
    conn.commit()
    conn.close()

#delete used for testing purposes
def delete(email):
    conn = sqlite3.connect(DB)
    conn.execute(
        "DELETE FROM subscribers WHERE email=?",(email,)
    )
    conn.execute(
        "DELETE FROM seen_jobs WHERE subscriber=?",(email,)
    )
    conn.commit()
    conn.close()
