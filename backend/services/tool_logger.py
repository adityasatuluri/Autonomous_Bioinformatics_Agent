import sqlite3
from datetime import datetime
import json
from configs.settings import Config
from backend.services.db_init import get_db_connection

def log_tool_execution(job_id, tool_name, status, message):
    """Logs tool execution to the SQLite tool_logs table."""
    # If job_id is not provided, use 0 for system/test logs
    job_id = job_id or 0
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO tool_logs (job_id, tool_name, status, message) VALUES (?, ?, ?, ?)",
            (job_id, tool_name, status, str(message))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log tool execution: {e}")

def create_structured_response(status, data=None, error=None, provenance=None):
    """Creates a standard structured tool response."""
    response = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if data is not None:
        response["data"] = data
    if error is not None:
        response["error"] = error
    if provenance is not None:
        response["provenance"] = provenance
        
    return json.dumps(response)
