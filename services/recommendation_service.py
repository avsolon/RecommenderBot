from db import get_connection
import random


def add_recommendation(user_id, category, title, comment):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO recommendations (user_id, category, title, comment) VALUES (?, ?, ?, ?)",
                   (user_id, category, title, comment))
    conn.commit()
    conn.close()


def get_all(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, category, title FROM recommendations WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_random(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category, title, comment FROM recommendations WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return random.choice(rows) if rows else None


def delete_by_id(user_id, rec_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recommendations WHERE id=? AND user_id=?", (rec_id, user_id))
    conn.commit()
    conn.close()


def update_field(user_id, rec_id, field, value):
    if field not in ["category", "title", "comment"]:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE recommendations SET {field}=? WHERE id=? AND user_id=?",
                   (value, rec_id, user_id))
    conn.commit()
    conn.close()
