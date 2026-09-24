import pytest
import pandas as pd
import json
from backend.app import app
from backend.services.dataset import DatasetManager
from backend.services.analysis import StatisticalAnalyzer
from mcp_servers.dataset_mcp.tools import get_sample_groups, profile_dataset
from mcp_servers.analysis_mcp.tools import run_statistics

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_dataset_manager_group_detection():
    manager = DatasetManager()
    groups = manager.get_sample_groups()
    assert "Healthy" in groups
    assert "Breast" in groups
    assert "Lung" in groups
    assert "Unknown" not in groups

def test_dataset_manager_profile():
    manager = DatasetManager()
    profile = manager.profile_dataset()
    assert profile["total_metadata_samples"] > 0
    assert not profile["missing_values_detected"]
    assert profile["duplicate_columns_in_expression"] == 0

def test_statistical_analyzer():
    manager = DatasetManager()
    meta, expr = manager.load_dataset("Healthy", "Breast")
    
    analyzer = StatisticalAnalyzer(meta, expr)
    a_s, b_s = analyzer._validate_groups("Healthy", "Breast")
    assert len(a_s) > 0 and len(b_s) > 0
    
    res = analyzer.run_analysis("Healthy", "Breast", top_n=5)
    assert len(res) == 5
    assert "gene_id" in res[0]
    assert "adjusted_p_value" in res[0]

def test_api_status(client):
    rv = client.get('/api/status')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['status'] == 'online'

def test_api_groups(client):
    rv = client.get('/api/groups')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert "groups" in json_data["data"]
    
def test_reactome_mcp_handler():
    from mcp_servers.reactome_mcp.tools import find_pathways
    # Test empty input handling
    res = find_pathways.invoke({"gene_ids": []})
    data = json.loads(res)
    assert data["status"] == "error"
    
def test_end_to_end_mcp_flow():
    # 1. Dataset MCP
    groups_res = get_sample_groups.invoke({"job_id": 0})
    groups_data = json.loads(groups_res)
    assert groups_data["status"] == "success"
    assert "Breast" in groups_data["data"]["groups"]

def test_pubmed_mcp_empty_input():
    from mcp_servers.pubmed_mcp.tools import verify_biomarkers
    res = verify_biomarkers.invoke({"gene_ids": [], "disease": "Breast cancer"})
    data = json.loads(res)
    assert data["status"] == "error"

def test_checkpoint_manager_and_decision_endpoint(client):
    from backend.services.checkpoint_manager import request_decision, submit_decision
    import threading
    import time

    job_id = 9999
    # Simulate a background thread requesting decision
    def worker():
        opts = [{"key": "opt_a", "label": "Option A", "description": "Desc A"}]
        return request_decision(
            job_id=job_id,
            checkpoint_type="sample_qc",
            title="Test Checkpoint",
            description="Testing decision gate",
            options=opts,
            default_key="opt_a",
            timeout_seconds=5
        )

    t = threading.Thread(target=worker)
    t.start()
    
    # Wait for thread to enter wait state
    time.sleep(0.5)

    # Call decision endpoint via test client
    rv = client.post(f'/api/jobs/{job_id}/decision', json={"decision": "opt_a"})
    assert rv.status_code == 200
    res_data = rv.get_json()
    assert res_data["status"] == "success"
    assert res_data["decision"] == "opt_a"

    t.join(timeout=2)
    assert not t.is_alive()

def test_pharmacology_mcp():
    from mcp_servers.pharmacology_mcp.tools import query_drug_interactions
    # Test empty input
    res_err = query_drug_interactions.invoke({"gene_ids": []})
    data_err = json.loads(res_err)
    assert data_err["status"] == "error"

    # Test valid query (will hit DGIdb or fallback gracefully)
    res_valid = query_drug_interactions.invoke({"gene_ids": ["ENSG00000146648", "ENSG00000141510"], "disease": "Breast cancer"})
    data_valid = json.loads(res_valid)
    assert data_valid["status"] == "success"
    assert "interactions" in data_valid["data"]

def test_string_mcp():
    from mcp_servers.string_mcp.tools import query_ppi_network
    # Test empty input
    res_err = query_ppi_network.invoke({"gene_ids": []})
    data_err = json.loads(res_err)
    assert data_err["status"] == "error"

    # Test valid query (will hit STRING DB or fallback gracefully)
    res_valid = query_ppi_network.invoke({"gene_ids": ["ENSG00000146648", "ENSG00000141510", "ENSG00000012048"]})
    data_valid = json.loads(res_valid)
    assert data_valid["status"] == "success"
    assert "top_interactions" in data_valid["data"]
    assert "hub_gene" in data_valid["data"]

def test_secretion_mcp():
    from mcp_servers.secretion_mcp.tools import query_cellular_secretion
    res_err = query_cellular_secretion.invoke({"gene_ids": []})
    data_err = json.loads(res_err)
    assert data_err["status"] == "error"

    res_valid = query_cellular_secretion.invoke({"gene_ids": ["TIMP1", "MMP9", "TP53"]})
    data_valid = json.loads(res_valid)
    assert data_valid["status"] == "success"
    assert "secretion_profiles" in data_valid["data"]
    assert len(data_valid["data"]["secretion_profiles"]) == 3

def test_survival_mcp():
    from mcp_servers.survival_mcp.tools import query_survival_prognosis
    res_err = query_survival_prognosis.invoke({"gene_ids": []})
    data_err = json.loads(res_err)
    assert data_err["status"] == "error"

    res_valid = query_survival_prognosis.invoke({"gene_ids": ["VEGFA", "TP53"], "disease": "Breast cancer"})
    data_valid = json.loads(res_valid)
    assert data_valid["status"] == "success"
    assert "prognostic_profiles" in data_valid["data"]
    assert len(data_valid["data"]["prognostic_profiles"]) == 2

def test_security_headers(client):
    rv = client.get('/api/status')
    assert rv.status_code == 200
    assert rv.headers.get('X-Content-Type-Options') == 'nosniff'
    assert rv.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    assert rv.headers.get('X-XSS-Protection') == '1; mode=block'
    assert rv.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
    assert 'Content-Security-Policy' in rv.headers

def test_api_create_job_input_validations(client):
    # 1. Non-JSON body
    rv = client.post('/api/jobs', data="not json", content_type="text/plain")
    assert rv.status_code == 400
    assert "application/json" in rv.get_json()["message"]

    # 2. Missing groups
    rv = client.post('/api/jobs', json={"question": "Valid research question?"})
    assert rv.status_code == 400
    assert "required" in rv.get_json()["message"]

    # 3. Identical comparison groups
    rv = client.post('/api/jobs', json={
        "group_a": "Healthy",
        "group_b": "Healthy",
        "question": "What are the differences between Healthy and Healthy?"
    })
    assert rv.status_code == 400
    assert "distinct" in rv.get_json()["message"].lower()

    # 4. Unknown/invalid group
    rv = client.post('/api/jobs', json={
        "group_a": "Healthy",
        "group_b": "MartianTumor",
        "question": "What are the differences?"
    })
    assert rv.status_code == 400
    assert "Unknown group_b" in rv.get_json()["message"]

    # 5. Question too short (< 5 chars)
    rv = client.post('/api/jobs', json={
        "group_a": "Healthy",
        "group_b": "Breast",
        "question": "Why?"
    })
    assert rv.status_code == 400
    assert "at least 5 characters" in rv.get_json()["message"]

    # 6. Question too long (> 2000 chars)
    oversized_q = "A" * 2005
    rv = client.post('/api/jobs', json={
        "group_a": "Healthy",
        "group_b": "Breast",
        "question": oversized_q
    })
    assert rv.status_code == 400
    assert "exceeds maximum allowed limit" in rv.get_json()["message"]

    # 7. Unsupported or path traversal dataset name
    rv = client.post('/api/jobs', json={
        "group_a": "Healthy",
        "group_b": "Breast",
        "question": "Valid question here?",
        "dataset": "../../etc/passwd"
    })
    assert rv.status_code == 400
    assert "Unsupported or invalid dataset" in rv.get_json()["message"]

def test_api_decision_validations(client):
    # 1. Invalid job_id
    rv = client.post('/api/jobs/0/decision', json={"decision": "strict_power"})
    assert rv.status_code == 400

    # 2. Non-existent job_id
    rv = client.post('/api/jobs/999999/decision', json={"decision": "strict_power"})
    assert rv.status_code == 404

    # 3. Missing decision
    rv = client.post('/api/jobs/1/decision', json={})
    assert rv.status_code in [400, 404]

def test_dataset_manager_distinct_group_enforcement():
    from backend.services.dataset import DatasetManager
    import pytest
    manager = DatasetManager()
    with pytest.raises(ValueError, match="distinct"):
        manager.load_dataset("Healthy", "Healthy")



