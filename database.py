import sqlite3
import os

def init_db():
    """Initialize the SQLite database for movie matching functionality"""
    db_path = os.path.join(os.path.dirname(__file__), 'movie_match.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create match rooms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_rooms (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            library_filter TEXT DEFAULT 'Movies',
            min_participants INTEGER DEFAULT 2
        )
    ''')
    
    # Create room users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS room_users (
            room_id TEXT,
            user_id TEXT,
            username TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (room_id, user_id),
            FOREIGN KEY (room_id) REFERENCES match_rooms(id) ON DELETE CASCADE
        )
    ''')
    
    # Create movie swipes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movie_swipes (
            room_id TEXT,
            user_id TEXT,
            movie_id TEXT,
            movie_title TEXT,
            movie_year INTEGER,
            swipe_direction TEXT CHECK(swipe_direction IN ('left', 'right', 'super')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (room_id, user_id, movie_id),
            FOREIGN KEY (room_id) REFERENCES match_rooms(id) ON DELETE CASCADE
        )
    ''')
    
    # Create index for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_room_swipes ON movie_swipes(room_id, movie_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_swipes ON movie_swipes(room_id, user_id)')
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized at: {db_path}")

def get_db_connection():
    """Get a database connection"""
    db_path = os.path.join(os.path.dirname(__file__), 'movie_match.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn

if __name__ == "__main__":
    init_db()
