import os
import zipfile
import shutil
from pathlib import Path
from fastapi import UploadFile

IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}

async def extract_and_read(temp_dir: Path, upload_files: list[UploadFile]) -> list[tuple[str, str | None]]:
    """
    Extracts uploads to a temp directory and reads text files.
    Returns a list of (relative_path, content).
    If a file fails UTF-8 decoding, content is None.
    """
    if len(upload_files) == 1 and upload_files[0].filename.endswith(".zip"):
        zip_path = temp_dir / "upload.zip"
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(upload_files[0].file, f)
        
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
            
        os.remove(zip_path)
    else:
        for uf in upload_files:
            file_path = temp_dir / uf.filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(uf.file, f)
                
    results = []
    
    for root, dirs, files in os.walk(temp_dir):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file_name in files:
            file_path = Path(root) / file_name
            rel_path = str(file_path.relative_to(temp_dir)).replace("\\", "/")
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                results.append((rel_path, content))
            except UnicodeDecodeError:
                # Could be a binary file
                results.append((rel_path, None))
                
    return results
