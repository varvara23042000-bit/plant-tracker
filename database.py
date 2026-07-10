import sqlite3
from datetime import datetime

DB_FILE = "plants.db"


class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.init_db()

    def init_db(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                species TEXT,
                last_watered TEXT NOT NULL,
                frequency INTEGER NOT NULL DEFAULT 7,
                notes TEXT,
                image_path TEXT
            )
        """)
        self.conn.commit()

    def get_all(self):
        return self.conn.execute(
            "SELECT * FROM plants ORDER BY name"
        ).fetchall()

    def get_by_id(self, plant_id):
        return self.conn.execute(
            "SELECT * FROM plants WHERE id = ?", (plant_id,)
        ).fetchone()

    def insert(self, data):
        cur = self.conn.execute("""
            INSERT INTO plants (name, species, last_watered, frequency, notes, image_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get("name", ""),
            data.get("species", ""),
            data.get("last_watered", datetime.now().strftime("%Y-%m-%d")),
            data.get("frequency", 7),
            data.get("notes", ""),
            data.get("image_path", "")
        ))
        self.conn.commit()
        return cur.lastrowid

    def update(self, data):
        self.conn.execute("""
            UPDATE plants SET name=?, species=?, last_watered=?, frequency=?, notes=?, image_path=? WHERE id=?
        """, (
            data["name"], data.get("species", ""),
            data.get("last_watered", datetime.now().strftime("%Y-%m-%d")),
            data.get("frequency", 7), data.get("notes", ""),
            data.get("image_path", ""), data["id"]
        ))
        self.conn.commit()

    def delete(self, plant_id):
        self.conn.execute("DELETE FROM plants WHERE id=?", (plant_id,))
        self.conn.commit()

    def water(self, plant_id, date=None):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        self.conn.execute("UPDATE plants SET last_watered=? WHERE id=?", (date, plant_id))
        self.conn.commit()

    def needing_water(self):
        today = datetime.now().date()
        result = []
        for p in self.get_all():
            last = datetime.strptime(p["last_watered"], "%Y-%m-%d").date()
            days = (today - last).days
            if days > p["frequency"]:
                p = dict(p)
                p["overdue"] = days - p["frequency"]
                result.append(p)
        return result

    def close(self):
        if self.conn:
            self.conn.close()
