import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

from .extract import extract_and_read, UploadTooLargeError
from .reviewer import review
from .provider import VertexProvider

app = FastAPI()

# Assuming frontend is next to backend in the project root
frontend_dir = Path(__file__).parent.parent / "frontend"

@app.post("/api/review")
async def review_endpoint(files: list[UploadFile] = File(...)):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            scanned_files_data, synthetic_findings = await extract_and_read(Path(temp_dir), files)
            provider = VertexProvider()
            verdict = await review(scanned_files_data, synthetic_findings, provider)
            return verdict.model_dump()
    except UploadTooLargeError as e:
        return JSONResponse(status_code=413, content={"error": str(e)})
    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": "Reviewer failed. Try again."})

# Serve static files, but explicitly serve index.html for root
@app.get("/")
async def serve_index():
    return FileResponse(frontend_dir / "index.html")

app.mount("/", StaticFiles(directory=frontend_dir), name="static")
