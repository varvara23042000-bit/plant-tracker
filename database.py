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
        cursor = self.conn.cursor()
        cursor.execute("""
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
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, species, last_watered, frequency, notes, image_path FROM plants ORDER BY name")
        return cursor.fetchall()

    def get_plant_by_id(self, plant_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, species, last_watered, frequency, notes, image_path FROM plants WHERE id = ?", (plant_id,))
        return cursor.fetchone()

    def insert_plant(self, data):
        cursor = self.conn.cursor()
        cursor.execute("""
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
        return cursor.lastrowid

    def update_plant(self, data):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE plants SET name=?, species=?, last_watered=?, frequency=?, notes=?, image_path=? WHERE id=?
        """, (
            data.get("name", ""),
            data.get("species", ""),
            data.get("last_watered", datetime.now().strftime("%Y-%m-%d")),
            data.get("frequency", 7),
            data.get("notes", ""),
            data.get("image_path", ""),
            data["id"]
        ))
        self.conn.commit()

    def delete_plant(self, plant_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM plants WHERE id=?", (plant_id,))
        self.conn.commit()

    def update_watering_date(self, plant_id, new_date=None):
        if new_date is None:
            new_date = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute("UPDATE plants SET last_watered = ? WHERE id = ?", (new_date, plant_id))
        self.conn.commit()

    def get_plants_needing_water(self):
        today = datetime.now().date()
        needing = []
        for plant in self.get_all():
            last = datetime.strptime(plant["last_watered"], "%Y-%m-%d").date()
            days = (today - last).days
            if days > plant["frequency"]:
                p = dict(plant)
                p["days_overdue"] = days - plant["frequency"]
                needing.append(p)
        return needing

    def close(self):
        if self.conn:
            self.conn.close()
