import os
import zipfile
import shutil
from pathlib import Path
from fastapi import UploadFile

from .secrets import scan_for_secrets

IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}
MAX_TOTAL_SIZE = 50 * 1024 * 1024
MAX_FILE_SIZE = 1 * 1024 * 1024
KNOWN_BINARIES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tar", ".gz", ".exe", ".bin", ".so", ".dylib", ".dll"}

class UploadTooLargeError(Exception):
    pass

async def extract_and_read(temp_dir: Path, upload_files: list[UploadFile]) -> tuple[list[dict], list[dict]]:
    """
    Extracts uploads, scans for secrets, and builds manifest info.
    Returns: (scanned_files_data, synthetic_findings)
    """
    total_size = 0
    
    if len(upload_files) == 1 and upload_files[0].filename.endswith(".zip"):
        zip_path = temp_dir / "upload.zip"
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(upload_files[0].file, f)
            
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Check size before extraction, but only count files that will
            # actually be processed (i.e. not in an ignored directory).
            # This ensures .venv / .git / node_modules don't burn the budget.
            for info in zip_ref.infolist():
                parts = Path(info.filename).parts
                if any(part in IGNORE_DIRS for part in parts):
                    continue
                total_size += info.file_size
                if total_size > MAX_TOTAL_SIZE:
                    raise UploadTooLargeError("Upload exceeds 50 MB limit.")

            zip_ref.extractall(temp_dir)
            
        os.remove(zip_path)
    else:
        for uf in upload_files:
            parts = Path(uf.filename).parts
            if any(part in IGNORE_DIRS for part in parts):
                continue
            file_path = temp_dir / uf.filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb") as f:
                while chunk := await uf.read(8192):
                    total_size += len(chunk)
                    if total_size > MAX_TOTAL_SIZE:
                        raise UploadTooLargeError("Upload exceeds 50 MB limit.")
                    f.write(chunk)
                
    scanned_files_data = []
    synthetic_findings = []
    
    for root, dirs, files in os.walk(temp_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file_name in files:
            file_path = Path(root) / file_name
            rel_path = str(file_path.relative_to(temp_dir)).replace("\\", "/")
            
            size_bytes = os.path.getsize(file_path)
            ext = file_path.suffix.lower()
            
            file_data = {
                "path": rel_path,
                "size_bytes": size_bytes,
                "redacted": False,
                "truncated": False,
                "skipped": False,
                "skip_reason": None,
                "content": None,
                "original_content": None,
            }
            
            if ext in KNOWN_BINARIES:
                file_data["skipped"] = True
                file_data["skip_reason"] = "binary file"
                scanned_files_data.append(file_data)
                continue
                
            read_size = size_bytes
            if size_bytes > MAX_FILE_SIZE:
                read_size = MAX_FILE_SIZE
                file_data["truncated"] = True
                
            try:
                with open(file_path, "rb") as f:
                    raw_content = f.read(read_size)
                    
                file_data["original_content"] = raw_content
                
                decoded_content = None
                for encoding in ["utf-8", "utf-16le", "utf-16be"]:
                    try:
                        decoded_content = raw_content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                        
                if decoded_content is None:
                    file_data["skipped"] = True
                    file_data["skip_reason"] = "non-text content"
                    scanned_files_data.append(file_data)
                    continue
                    
                redacted_content, file_findings = scan_for_secrets(rel_path, decoded_content)
                if file_findings:
                    file_data["redacted"] = True
                    synthetic_findings.extend(file_findings)
                    
                file_data["content"] = redacted_content
                scanned_files_data.append(file_data)
                
            except Exception as e:
                file_data["skipped"] = True
                file_data["skip_reason"] = f"read error: {str(e)}"
                scanned_files_data.append(file_data)
                
    return scanned_files_data, synthetic_findings
