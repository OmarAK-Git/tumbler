import tempfile
import uuid
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

from .extract import extract_and_read, UploadTooLargeError
from .reviewer import review
from .provider import VertexProvider
from .evidence_bundle import build_evidence_bundle
from .crucible_handoff import write_handoff

logger = logging.getLogger(__name__)

app = FastAPI()

# V1 assumption: in-memory only, lost on restart, no eviction.
# Sessions are pushable for as long as the Tumbler process stays alive.
ACTIVE_SESSIONS: dict[str, dict] = {}

# Assuming frontend is next to backend in the project root
frontend_dir = Path(__file__).parent.parent / "frontend"

@app.post("/api/review")
async def review_endpoint(files: list[UploadFile] = File(...)):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            scanned_files_data, synthetic_findings = await extract_and_read(Path(temp_dir), files)
            provider = VertexProvider()
            verdict = await review(scanned_files_data, synthetic_findings, provider)
            
            # Pre-build corpus bundle for handoff caching
            evidence_bundle = build_evidence_bundle(scanned_files_data)
            
            session_id = str(uuid.uuid4())
            ACTIVE_SESSIONS[session_id] = {
                "session_id": session_id,
                "verdict": verdict.verdict,
                "corpus_bundle": evidence_bundle
            }
            
            verdict_dict = verdict.model_dump()
            verdict_dict["session_id"] = session_id
            return verdict_dict
            
    except UploadTooLargeError as e:
        return JSONResponse(status_code=413, content={"error": str(e)})
    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": "Reviewer failed. Try again."})

@app.post("/api/sessions/{id}/push-to-crucible")
async def push_to_crucible_endpoint(id: str):
    # PASS-only gating rationale:
    # Crucible is for hardening new-feature prompts against clean codebases.
    # Address the FIX findings before pushing to Crucible.
    if id not in ACTIVE_SESSIONS:
        return JSONResponse(
            status_code=404,
            content={"error": "Session no longer available — please re-run the review."}
        )
    
    session_data = ACTIVE_SESSIONS[id]
    if session_data["verdict"] != "PASS":
        return JSONResponse(
            status_code=400,
            content={"error": "Crucible push is only available for PASS verdicts. Address the FIX findings first."}
        )
    
    try:
        handoff_path = write_handoff(
            session_id=id,
            corpus_bundle=session_data["corpus_bundle"],
            tumbler_verdict=session_data["verdict"]
        )
        return {"handoff_path": str(handoff_path)}
    except Exception as e:
        logger.exception("Failed to write Crucible handoff")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to write handoff: {str(e)}"}
        )

# Serve static files, but explicitly serve index.html for root
@app.get("/")
async def serve_index():
    return FileResponse(frontend_dir / "index.html")

app.mount("/", StaticFiles(directory=frontend_dir), name="static")
