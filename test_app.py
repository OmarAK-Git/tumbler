import os
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_empty_readme():
    files = {
        'files': ('README.md', b'# Just a readme', 'text/markdown')
    }
    response = client.post("/api/review", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "verdict" in data
    assert data["verdict"] in ["PASS", "FIX"]
    if data["verdict"] == "FIX":
        # Missing evidence should trigger FIX
        assert "findings" in data

def test_hardcoded_secret():
    code_with_secret = b'''
    def get_db():
        aws_access_key = "AKIAIOSFODNN7EXAMPLE"
        return aws_access_key
    '''
    files = [
        ('files', ('main.py', code_with_secret, 'text/x-python'))
    ]
    response = client.post("/api/review", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "verdict" in data
    # Secret should cause it to fail
    assert data["verdict"] == "FIX"
    findings_str = str(data["findings"]).lower()
    assert "secret" in findings_str or "aws" in findings_str or "key" in findings_str

def test_small_app():
    files = [
        ('files', ('main.py', b'print("hello world")', 'text/x-python')),
        ('files', ('evidence/test-results.txt', b'1 passed', 'text/plain'))
    ]
    response = client.post("/api/review", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "verdict" in data
    # Should be valid JSON schema parsed correctly
    assert data["verdict"] in ["PASS", "FIX"]
