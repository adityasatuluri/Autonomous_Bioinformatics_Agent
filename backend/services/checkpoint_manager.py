import json
import threading
from typing import List, Dict, Any, Optional
from backend.services.db_init import get_db_connection
from backend.services.tool_logger import log_tool_execution

# In-memory thread synchronization registry
_active_events: Dict[int, threading.Event] = {}
_active_decisions: Dict[int, str] = {}
_lock = threading.Lock()

def request_decision(
    job_id: int,
    checkpoint_type: str,
    title: str,
    description: str,
    options: List[Dict[str, str]],
    default_key: str,
    timeout_seconds: int = 180
) -> str:
    """
    Halts the orchestrator thread and pauses the job at a Human-in-the-Loop decision gate.
    Waits for the researcher to submit a decision from the dashboard or defaults after timeout.
    """
    conn = get_db_connection()
    try:
        options_json = json.dumps(options)
        conn.execute(
            """
            INSERT INTO checkpoints (job_id, checkpoint_type, title, description, options, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
            """,
            (job_id, checkpoint_type, title, description, options_json)
        )
        conn.execute("UPDATE jobs SET status = 'waiting_for_input' WHERE id = ?", (job_id,))
        conn.commit()
    finally:
        conn.close()

    log_tool_execution(
        job_id, 
        f"decision_gate.{checkpoint_type}", 
        "info", 
        f"Paused at checkpoint '{title}'. Awaiting researcher confirmation."
    )

    event = threading.Event()
    with _lock:
        _active_events[job_id] = event
        _active_decisions.pop(job_id, None)

    # Block thread until frontend submits decision or timeout expires
    signaled = event.wait(timeout=timeout_seconds)

    with _lock:
        if signaled and job_id in _active_decisions:
            decision = _active_decisions[job_id]
            log_tool_execution(
                job_id, 
                f"decision_gate.{checkpoint_type}", 
                "success", 
                f"Researcher confirmed action: '{decision}'"
            )
        else:
            decision = default_key
            log_tool_execution(
                job_id, 
                f"decision_gate.{checkpoint_type}", 
                "info", 
                f"Checkpoint timed out ({timeout_seconds}s). Auto-selected recommended default: '{decision}'"
            )

        # Cleanup memory
        _active_events.pop(job_id, None)
        _active_decisions.pop(job_id, None)

    # Update database record
    conn = get_db_connection()
    try:
        conn.execute(
            """
            UPDATE checkpoints 
            SET status = 'resolved', selected_option = ? 
            WHERE job_id = ? AND status = 'pending'
            """,
            (decision, job_id)
        )
        conn.execute("UPDATE jobs SET status = 'running' WHERE id = ?", (job_id,))
        conn.commit()
    finally:
        conn.close()

    return decision

def submit_decision(job_id: int, decision: str) -> bool:
    """
    Submits a researcher's decision from the API/UI to resume the paused background analysis thread.
    """
    with _lock:
        if job_id in _active_events:
            _active_decisions[job_id] = decision
            _active_events[job_id].set()
            return True
            
    # Fallback DB update if thread already terminated or disconnected
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE checkpoints SET status = 'resolved', selected_option = ? WHERE job_id = ? AND status = 'pending'",
            (decision, job_id)
        )
        conn.commit()
    finally:
        conn.close()
    return False

def get_pending_checkpoint(job_id: int) -> Optional[Dict[str, Any]]:
    """Fetch active pending checkpoint for a job."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM checkpoints WHERE job_id = ? AND status = 'pending' ORDER BY id DESC LIMIT 1",
            (job_id,)
        ).fetchone()
        if row:
            res = dict(row)
            res["options"] = json.loads(res["options"])
            return res
    finally:
        conn.close()
    return None
