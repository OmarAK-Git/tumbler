from fastapi.testclient import TestClient
from pathlib import Path
from backend.main import app, ACTIVE_SESSIONS

client = TestClient(app)

def test_push_endpoint_scenarios():
    # 1. PASS verdict + session in cache -> 200 + handoff path
    session_id_pass = "session-pass-123-test"
    ACTIVE_SESSIONS[session_id_pass] = {
        "session_id": session_id_pass,
        "verdict": "PASS",
        "corpus_bundle": "<evidence>clean codebase</evidence>"
    }
    
    expected_path = Path.home() / ".crucible" / "incoming" / f"{session_id_pass}.json"
    if expected_path.exists():
        expected_path.unlink()
        
    try:
        response = client.post(f"/api/sessions/{session_id_pass}/push-to-crucible")
        assert response.status_code == 200
        data = response.json()
        assert "handoff_path" in data
        assert Path(data["handoff_path"]) == expected_path
        assert expected_path.exists()
    finally:
        if expected_path.exists():
            expected_path.unlink()
            
    # 2. PASS verdict + session NOT in cache -> 404 with plain-language error
    response_404 = client.post("/api/sessions/nonexistent-session/push-to-crucible")
    assert response_404.status_code == 404
    data_404 = response_404.json()
    assert "Session no longer available — please re-run the review." in data_404["error"]
    
    # 3. FIX verdict + session in cache -> 400 with plain-language error
    session_id_fix = "session-fix-123-test"
    ACTIVE_SESSIONS[session_id_fix] = {
        "session_id": session_id_fix,
        "verdict": "FIX",
        "corpus_bundle": "<evidence>messy codebase</evidence>"
    }
    
    response_400 = client.post(f"/api/sessions/{session_id_fix}/push-to-crucible")
    assert response_400.status_code == 400
    data_400 = response_400.json()
    assert "Crucible push is only available for PASS verdicts" in data_400["error"]
