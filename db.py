import sqlite3
import config
import os

DB_NAME = config.DATABASE_PATH

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                comment TEXT,
                date_added DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print(f"База данных инициализирована: {os.path.abspath(DB_NAME)}")

def add_recommendation(user_id, category, title, comment):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO recommendations (user_id, category, title, comment) VALUES (?, ?, ?, ?)",
            (user_id, category, title, comment)
        )
        conn.commit()
        return cursor.lastrowid

def get_recommendations(user_id, category=None, limit=None, offset=0):
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT id, category, title, comment, date_added FROM recommendations WHERE user_id = ?"
        params = [user_id]
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY date_added DESC"
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        cursor.execute(query, params)
        return cursor.fetchall()

def get_recommendation_by_id(user_id, rec_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, category, title, comment, date_added FROM recommendations WHERE id = ? AND user_id = ?",
            (rec_id, user_id)
        )
        return cursor.fetchone()

def search_recommendations(user_id, keyword, category=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT id, category, title, comment, date_added FROM recommendations WHERE user_id = ? AND (title LIKE ? OR comment LIKE ?)"
        params = [user_id, f"%{keyword}%", f"%{keyword}%"]
        if category:
            query += " AND category = ?"
            params.append(category)
        cursor.execute(query, params)
        return cursor.fetchall()

def update_recommendation(user_id, rec_id, field, new_value):
    allowed_fields = ['category', 'title', 'comment']
    if field not in allowed_fields:
        return False
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE recommendations SET {field} = ? WHERE id = ? AND user_id = ?",
            (new_value, rec_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def delete_recommendation(user_id, rec_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM recommendations WHERE id = ? AND user_id = ?",
            (rec_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def get_random_recommendation(user_id, category=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT id, category, title, comment FROM recommendations WHERE user_id = ?"
        params = [user_id]
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY RANDOM() LIMIT 1"
        cursor.execute(query, params)
        return cursor.fetchone()