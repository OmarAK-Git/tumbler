from typing import Literal, Annotated
from pydantic import BaseModel, Field

class RubricResult(BaseModel):
    category: str
    status: str
    reasoning: str

class ScannedFile(BaseModel):
    path: str
    size_bytes: int
    redacted: bool
    truncated: bool
    skipped: bool
    skip_reason: str | None

class PassVerdict(BaseModel):
    verdict: Literal["PASS"]
    summary: str
    evidence_relied_on: list[str]
    rubric_results: list[RubricResult]
    scanned: list[ScannedFile]

class Finding(BaseModel):
    severity: Literal["blocker", "major", "minor"]
    category: Literal["security", "correctness", "spec_alignment", "missing_evidence", "secrets", "tests", "prompt_injection_attempt"]
    file: str
    line: int | None = None
    description: str
    why_it_matters: str

class EvidenceCollectionCommand(BaseModel):
    command_or_action: str
    produces: str

class AntigravityPrompt(BaseModel):
    objective: str
    constraints: list[str]
    acceptance_criteria: list[str]
    evidence_collection: list[EvidenceCollectionCommand]

class FixVerdict(BaseModel):
    verdict: Literal["FIX"]
    summary: str
    findings: list[Finding]
    antigravity_prompt: AntigravityPrompt
    scanned: list[ScannedFile]

Verdict = Annotated[PassVerdict | FixVerdict, Field(discriminator="verdict")]
