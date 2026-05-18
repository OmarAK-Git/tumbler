import hashlib

def build_evidence_bundle(scanned_files_data: list[dict]) -> str:
    """
    Builds the evidence bundle string to send to the LLM.
    Expects a list of dictionaries, each containing:
    - path: str
    - content: str | None (redacted if applicable)
    - original_content: bytes | None
    - redacted: bool
    - skipped: bool
    - skip_reason: str | None
    - truncated: bool
    - size_bytes: int
    """
    bundle = ""
    
    for data in scanned_files_data:
        path = data["path"]
        skipped = data["skipped"]
        content = data["content"]
        
        if skipped:
            # The prompt says binary files are skipped but "their names so the reviewer knows screenshots exist"
            # It's better to just list them like in V1 or explicitly say skipped.
            # "listed in the manifest with their names so the reviewer knows screenshots exist" but "do not transmit its content to the LLM".
            # The spec says: binary files are listed by name but not transmitted.
            bundle += f"=== file: {path} ===\n[Skipped: {data.get('skip_reason', 'binary file')}]\n\n"
            continue
            
        original_content = data.get("original_content")
        if original_content is None:
            original_content = b""
            
        file_hash = hashlib.sha256(original_content).hexdigest()[:8]
        redacted_str = "true" if data.get("redacted") else "false"
        
        bundle += f'<evidence path="{path}" hash="{file_hash}" redacted="{redacted_str}">\n'
        bundle += content
        
        if data.get("truncated"):
            original_mb = data["size_bytes"] / (1024 * 1024)
            bundle += f"\n\n[truncated, original was {original_mb:.1f} MB]"
            
        bundle += f'\n</evidence>\n\n'
        
    return bundle
