import re
import json
import threading
from flask import Blueprint, jsonify, request
from configs.settings import Config
from mcp_servers.dataset_mcp.tools import get_sample_groups, profile_dataset
from backend.services.dataset import DatasetManager
from backend.services.db_init import get_db_connection
from backend.services.orchestrator import WorkflowOrchestrator
from backend.services.checkpoint_manager import submit_decision, get_pending_checkpoint

api_bp = Blueprint('api', __name__, url_prefix='/api')

def run_workflow_async(job_id: int, group_a: str, group_b: str, question: str):
    orchestrator = WorkflowOrchestrator()
    orchestrator.run_workflow(job_id, group_a, group_b, question)

@api_bp.route('/groups', methods=['GET'])
def get_groups():
    response = get_sample_groups.invoke({"job_id": 0})
    return jsonify(json.loads(response))

@api_bp.route('/dataset/profile', methods=['GET'])
def profile():
    response = profile_dataset.invoke({"job_id": 0})
    return jsonify(json.loads(response))

@api_bp.route('/jobs', methods=['POST'])
def create_job():
    # 1. Payload format validation
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid JSON payload; object expected"}), 400

    # 2. Dataset validation (whitelist and traversal protection)
    raw_dataset = data.get('dataset', 'GSE68086')
    if not isinstance(raw_dataset, str):
        return jsonify({"status": "error", "message": "dataset must be a string"}), 400
    dataset = raw_dataset.strip()
    if not dataset or dataset not in Config.ALLOWED_DATASETS:
        return jsonify({
            "status": "error",
            "message": f"Unsupported or invalid dataset. Allowed: {sorted(list(Config.ALLOWED_DATASETS))}"
        }), 400

    # 3. Group parameters validation
    raw_group_a = data.get('group_a')
    raw_group_b = data.get('group_b')

    if not isinstance(raw_group_a, str) or not isinstance(raw_group_b, str):
        return jsonify({"status": "error", "message": "group_a and group_b are required and must be valid strings"}), 400

    group_a = raw_group_a.strip()
    group_b = raw_group_b.strip()

    if not group_a or not group_b:
        return jsonify({"status": "error", "message": "Both group_a and group_b are required and cannot be empty"}), 400

    if group_a.lower() == group_b.lower():
        return jsonify({
            "status": "error",
            "message": "Comparison groups must be distinct biological cohorts (Group A cannot be identical to Group B)"
        }), 400

    try:
        valid_groups = DatasetManager().get_sample_groups()
        if group_a not in valid_groups:
            return jsonify({
                "status": "error",
                "message": f"Unknown group_a '{group_a}'. Available groups: {valid_groups}"
            }), 400
        if group_b not in valid_groups:
            return jsonify({
                "status": "error",
                "message": f"Unknown group_b '{group_b}'. Available groups: {valid_groups}"
            }), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to verify dataset groups: {str(e)}"}), 500

    # 4. Research question validation & sanitization
    raw_question = data.get('question')
    if not isinstance(raw_question, str):
        return jsonify({"status": "error", "message": "question is required and must be a string"}), 400

    question = raw_question.strip().replace('\x00', '')  # Remove null bytes

    if len(question) < Config.MIN_QUESTION_LENGTH:
        return jsonify({
            "status": "error",
            "message": f"Research question must be at least {Config.MIN_QUESTION_LENGTH} characters long"
        }), 400

    if len(question) > Config.MAX_QUESTION_LENGTH:
        return jsonify({
            "status": "error",
            "message": f"Research question exceeds maximum allowed limit of {Config.MAX_QUESTION_LENGTH} characters"
        }), 400

    # 5. Insert job into database with parameterized query
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO jobs (dataset, group_a, group_b, question, status) VALUES (?, ?, ?, ?, ?)",
        (dataset, group_a, group_b, question, "pending")
    )
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # 6. Start orchestration asynchronously in background thread
    thread = threading.Thread(target=run_workflow_async, args=(job_id, group_a, group_b, question))
    thread.daemon = True
    thread.start()

    return jsonify({"status": "success", "job_id": job_id}), 201

@api_bp.route('/jobs/<int:job_id>/decision', methods=['POST'])
def make_decision(job_id: int):
    if job_id <= 0:
        return jsonify({"status": "error", "message": "Invalid job ID"}), 400

    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    # Verify job existence and current state
    conn = get_db_connection()
    job = conn.execute("SELECT status FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    pending = get_pending_checkpoint(job_id)

    if not job and not pending:
        return jsonify({"status": "error", "message": f"Job {job_id} not found"}), 404

    if job and job["status"] != "waiting_for_input" and not pending:
        return jsonify({
            "status": "error",
            "message": f"Job {job_id} is not currently awaiting a decision (status: {job['status']})"
        }), 400

    raw_decision = data.get('decision')
    if not isinstance(raw_decision, str) or not raw_decision.strip():
        return jsonify({"status": "error", "message": "decision is required and must be a non-empty string"}), 400

    decision = raw_decision.strip()
    if len(decision) > 64 or not re.match(r'^[a-zA-Z0-9_\-]+$', decision):
        return jsonify({"status": "error", "message": "Invalid decision format"}), 400

    # Validate decision against allowed checkpoint options
    pending = get_pending_checkpoint(job_id)
    if pending and "options" in pending and isinstance(pending["options"], list):
        allowed_keys = {opt.get("key") for opt in pending["options"] if isinstance(opt, dict) and "key" in opt}
        if allowed_keys and decision not in allowed_keys:
            return jsonify({
                "status": "error",
                "message": f"Invalid decision '{decision}'. Allowed options: {sorted(list(allowed_keys))}"
            }), 400

    resumed = submit_decision(job_id, decision)
    return jsonify({
        "status": "success",
        "job_id": job_id,
        "decision": decision,
        "thread_resumed": resumed
    })

@api_bp.route('/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id: int):
    if job_id <= 0:
        return jsonify({"status": "error", "message": "Invalid job ID"}), 400

    conn = get_db_connection()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()

    if not job:
        conn.close()
        return jsonify({"status": "error", "message": "Job not found"}), 404

    result = dict(job)

    # Fetch logs for workflow trace
    logs = conn.execute("SELECT tool_name, status, message, timestamp FROM tool_logs WHERE job_id = ? ORDER BY id ASC", (job_id,)).fetchall()
    result["logs"] = [dict(l) for l in logs]

    # Fetch top 10 genes
    genes = conn.execute("SELECT * FROM analysis_results WHERE job_id = ? ORDER BY ABS(log2_fold_change) DESC LIMIT 10", (job_id,)).fetchall()
    result["genes"] = [dict(g) for g in genes]

    # Fetch top 5 pathways
    pathways = conn.execute("SELECT * FROM pathways WHERE job_id = ? ORDER BY significance ASC LIMIT 5", (job_id,)).fetchall()
    result["pathways"] = [dict(p) for p in pathways]

    # Fetch literature evidence
    lit = conn.execute("SELECT * FROM literature_evidence WHERE job_id = ? ORDER BY id ASC", (job_id,)).fetchall()
    result["literature_evidence"] = [dict(row) for row in lit]

    # Check if job is waiting for user decision
    if result["status"] == "waiting_for_input":
        result["pending_checkpoint"] = get_pending_checkpoint(job_id)

    # If completed, get the report
    if result["status"] == "completed":
        report = conn.execute("SELECT summary FROM reports WHERE job_id = ? ORDER BY id DESC LIMIT 1", (job_id,)).fetchone()
        if report:
            result["report"] = report["summary"]

    conn.close()
    return jsonify(result)


