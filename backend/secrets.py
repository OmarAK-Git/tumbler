import re

PATTERNS = {
    "aws_access_key": r"AKIA[0-9A-Z]{16}",
    "github_token": r"gh[pousr]_[A-Za-z0-9_]{36,}",
    "jwt": r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
    "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "generic_secret": r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][A-Za-z0-9+/=]{20,}['\"]",
}

def scan_for_secrets(file_path: str, content: str) -> tuple[str, list[dict]]:
    """
    Scans content for secrets, returning the redacted content and a list of synthetic findings.
    """
    if file_path.endswith(".env.example") or file_path == ".env.example":
        return content, []
        
    if "tests/fixtures/" in file_path or "tests/data/" in file_path:
        return content, []

    findings = []
    lines = content.split('\n')
    redacted_lines = []

    for i, line in enumerate(lines):
        current_line = line
        line_num = i + 1
        
        for secret_type, pattern in PATTERNS.items():
            matches = list(re.finditer(pattern, current_line))
            for match in matches:
                findings.append({
                    "severity": "blocker",
                    "category": "secrets",
                    "file": file_path,
                    "line": line_num,
                    "description": f"Hardcoded secret detected: {secret_type}. The secret value has been redacted from the reviewer's view, but remains in your source code.",
                    "why_it_matters": "Secrets in source code are credential exposures the moment the repo touches any remote. Remove the literal value, read from an environment variable at startup, and rotate the exposed credential."
                })
            
            if matches:
                current_line = re.sub(pattern, f"<REDACTED:{secret_type}>", current_line)

        redacted_lines.append(current_line)

    return '\n'.join(redacted_lines), findings
