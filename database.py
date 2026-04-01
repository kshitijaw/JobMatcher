# Shared DB used by app.py and worked.py
import psycopg2
import os

DB_URL = os.environ["DATABASE_URL"]

def get_conn():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id       SERIAL PRIMARY KEY,
            email    TEXT NOT NULL,
            role     TEXT NOT NULL,
            city     TEXT NOT NULL,
            resume   TEXT NOT NULL,
            active   INTEGER DEFAULT 1,
            created  TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS seen_jobs (
            job_id      TEXT NOT NULL,
            subscriber  TEXT NOT NULL,
            seen_at     TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (job_id, subscriber)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def add_subscriber(email, role, city, resume):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO subscribers (email, role, city, resume) VALUES (%s,%s,%s,%s)",
        (email, role, city, resume)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_subscribers():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT email, role, city, resume FROM subscribers WHERE active=1")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"email": r[0], "role": r[1], "city": r[2], "resume": r[3]} for r in rows]

def is_new_job(job_id, email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM seen_jobs WHERE job_id=%s AND subscriber=%s", (job_id, email)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row is None

def mark_seen(job_id, email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO seen_jobs (job_id, subscriber) VALUES (%s,%s) ON CONFLICT DO NOTHING",
        (job_id, email)
    )
    conn.commit()
    cur.close()
    conn.close()
