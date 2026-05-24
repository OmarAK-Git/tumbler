import json
from datetime import datetime, timezone
from pathlib import Path

def write_handoff(session_id: str, corpus_bundle: str, tumbler_verdict: str) -> Path:
    """
    Writes a handoff JSON file containing the clean corpus to ~/.crucible/incoming/<session_id>.json
    Creates parent directories if missing.
    """
    handoff_dir = Path.home() / ".crucible" / "incoming"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    
    handoff_path = handoff_dir / f"{session_id}.json"
    
    handoff_data = {
        "tumbler_session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "corpus_bundle": corpus_bundle,
        "source": "tumbler",
        "tumbler_verdict": tumbler_verdict
    }
    
    with open(handoff_path, "w", encoding="utf-8") as f:
        json.dump(handoff_data, f, indent=2, ensure_ascii=False)
        
    return handoff_path
