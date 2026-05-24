import json
import os
from pathlib import Path
from backend.crucible_handoff import write_handoff

def test_write_handoff_creation():
    session_id = "test-session-123-uuid"
    corpus_bundle = '<evidence path="main.py">\nprint("hello")\n</evidence>'
    verdict = "PASS"
    
    expected_path = Path.home() / ".crucible" / "incoming" / f"{session_id}.json"
    
    # Clean up if exists from a previous bad run
    if expected_path.exists():
        expected_path.unlink()
        
    try:
        written_path = write_handoff(session_id, corpus_bundle, verdict)
        assert written_path == expected_path
        assert written_path.exists()
        
        # Verify JSON schema and contents
        with open(written_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        assert data["tumbler_session_id"] == session_id
        assert "created_at" in data
        assert data["corpus_bundle"] == corpus_bundle
        assert data["source"] == "tumbler"
        assert data["tumbler_verdict"] == verdict
        
        # Verify round-trip matches
        assert data["corpus_bundle"] == corpus_bundle
    finally:
        # Cleanup
        if expected_path.exists():
            expected_path.unlink()
