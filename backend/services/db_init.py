import sqlite3
import os
from configs.settings import Config

def get_db_connection():
    """Establish a connection to the SQLite database."""
    db_path = os.path.join(Config.BASE_DIR, 'storage', 'app.db')
    
    # Ensure the storage directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database schema."""
    schema = '''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset TEXT NOT NULL,
        group_a TEXT NOT NULL,
        group_b TEXT NOT NULL,
        question TEXT,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS analysis_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        gene_id TEXT NOT NULL,
        group_a_mean REAL,
        group_b_mean REAL,
        log2_fold_change REAL,
        p_value REAL,
        adjusted_p_value REAL,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    );

    CREATE TABLE IF NOT EXISTS pathways (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        pathway_id TEXT NOT NULL,
        pathway_name TEXT NOT NULL,
        significance REAL,
        matched_entities INTEGER,
        token TEXT,
        source TEXT,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    );

    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        summary TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    );

    CREATE TABLE IF NOT EXISTS tool_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        tool_name TEXT NOT NULL,
        status TEXT NOT NULL,
        message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    );

    CREATE TABLE IF NOT EXISTS checkpoints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        checkpoint_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        options TEXT NOT NULL,
        selected_option TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    );

    CREATE TABLE IF NOT EXISTS literature_evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        gene_id TEXT NOT NULL,
        gene_symbol TEXT,
        disease TEXT NOT NULL,
        hit_count INTEGER NOT NULL,
        is_novel BOOLEAN NOT NULL,
        top_article_title TEXT,
        top_article_pmid TEXT,
        source TEXT,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    );
    '''
    
    conn = get_db_connection()
    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
