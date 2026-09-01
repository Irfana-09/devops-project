import sqlite3
import os

db_path = "users.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        # Check if the timestamp column exists
        cur.execute("PRAGMA table_info(bills)")
        columns = [col[1] for col in cur.fetchall()]
        
        if 'timestamp' not in columns:
            print("Adding 'timestamp' column to 'bills' table using table recreation...")
            
            # 1. Create a new table with the new schema
            cur.execute("""
            CREATE TABLE bills_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                units REAL,
                amount REAL,
                reading REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 2. Copy the data from the old table
            cur.execute("INSERT INTO bills_new (id, user_id, units, amount) SELECT id, user_id, units, amount FROM bills")
            
            # 3. Drop the old table
            cur.execute("DROP TABLE bills")
            
            # 4. Rename the new table
            cur.execute("ALTER TABLE bills_new RENAME TO bills")
            
            conn.commit()
            print("Successfully migrated 'bills' table with 'timestamp' column.")
        
        # Check if reading column exists (added for VoltWise)
        cur.execute("PRAGMA table_info(bills)")
        columns = [col[1] for col in cur.fetchall()]
        if 'reading' not in columns:
            print("Adding 'reading' column to 'bills' table...")
            cur.execute("ALTER TABLE bills ADD COLUMN reading REAL")
            conn.commit()
            print("Successfully added 'reading' column to 'bills' table.")
        else:
            print("'reading' column already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()