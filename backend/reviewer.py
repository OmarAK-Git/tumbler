import json
import logging
from pathlib import Path
from pydantic import TypeAdapter

from .schemas import Verdict, FixVerdict
from .provider import ReviewerProvider

logger = logging.getLogger(__name__)

VerdictAdapter = TypeAdapter(Verdict)

METHODOLOGY_PATH = Path(__file__).parent / "methodology.md"
if not METHODOLOGY_PATH.exists():
    raise FileNotFoundError("methodology.md is missing. It is required for the reviewer to run.")

with open(METHODOLOGY_PATH, "r", encoding="utf-8") as f:
    METHODOLOGY_TEXT = f.read()

ROLE_PROMPT = "You are a senior engineer reviewing a single application. Your output is one of two verdicts: PASS or FIX. There is no other option."

PASS_BAR_PROMPT = """PASS is honest, not generous. Tumbler issues PASS only when all of the following hold:
1. No secrets in code. No API keys, tokens, passwords, connection strings, or private keys in source files.
2. No security blockers. No SQL injection, no missing auth on protected routes, no obvious XSS, no insecure deserialization. (V1 scope: only obvious findings. Deep audits are out of scope.)
3. Spec alignment. If a spec/README/intent doc exists, the code matches it. If no spec exists, the FIX prompt is "write a one-paragraph intent statement and put it at the root."
4. Evidence of behavior. `/evidence/` contains at least one test result file and (for UI apps) at least one screenshot of the working app. Without evidence of behavior, the reviewer cannot honestly say the code does what it claims.
5. No hallucinated values. No TODOs in critical paths, no fake placeholder data in production code paths, no functions that obviously don't do what their names imply.
If any of these fails, verdict is FIX with that as the finding."""

VERDICT_SCHEMA_PROMPT = """You must output valid JSON matching the following schema.
For a PASS verdict:
{
  "verdict": "PASS",
  "summary": "string — what was reviewed and why it's good",
  "evidence_relied_on": ["evidence/test-results.txt", "evidence/login-screenshot.png", "..."],
  "rubric_results": [
    { "category": "secret_hygiene", "status": "clear", "reasoning": "..." },
    { "category": "security_blockers", "status": "clear", "reasoning": "..." },
    { "category": "spec_alignment", "status": "clear", "reasoning": "..." },
    { "category": "evidence_of_behavior", "status": "clear", "reasoning": "..." },
    { "category": "hallucinated_values", "status": "clear", "reasoning": "..." }
  ]
}

For a FIX verdict:
{
  "verdict": "FIX",
  "summary": "string — one paragraph on overall state",
  "findings": [
    {
      "severity": "blocker" | "major" | "minor",
      "category": "security" | "correctness" | "spec_alignment" | "missing_evidence" | "secrets" | "tests",
      "file": "path/to/file.py",
      "line": 42,
      "description": "string",
      "why_it_matters": "string"
    }
  ],
  "antigravity_prompt": {
    "objective": "string",
    "constraints": ["string", "string"],
    "acceptance_criteria": ["string", "string"],
    "evidence_collection": [
      { "command_or_action": "pytest tests/ > evidence/test-results.txt 2>&1", "produces": "evidence/test-results.txt" }
    ]
  }
}"""

EVIDENCE_CONVENTION_GUARDRAIL = """Before evaluating any other rubric category, check whether /evidence/ exists in the uploaded project and contains at least one file. If it does not, the verdict is FIX. The first finding must have category missing_evidence, severity blocker, and description noting the absence. The antigravity_prompt.evidence_collection field must include commands that create /evidence/ and populate it with the artifacts the methodology requires for this project type."""

ANTIGRAVITY_PROMPT_RULES = """When you produce a FIX prompt, scope it tightly. Reference specific files. Include hard constraints. Include evidence collection commands. Do not invite Antigravity to refactor anything not in the findings."""

SYSTEM_PROMPT = f"{ROLE_PROMPT}\n\n{PASS_BAR_PROMPT}\n\n{METHODOLOGY_TEXT}\n\n{VERDICT_SCHEMA_PROMPT}\n\n{EVIDENCE_CONVENTION_GUARDRAIL}\n\n{ANTIGRAVITY_PROMPT_RULES}"

async def review(files: list[tuple[str, str | None]], provider: ReviewerProvider) -> Verdict:
    evidence_bundle = ""
    for path, content in files:
        if content is None:
            # Binary or undecodable
            evidence_bundle += f"=== file: {path} ===\n[Binary or non-UTF-8 content]\n\n"
        else:
            evidence_bundle += f"=== file: {path} ===\n{content}\n\n"

    for attempt in range(2):
        try:
            parsed_json = await provider.review(SYSTEM_PROMPT, evidence_bundle)
            verdict = VerdictAdapter.validate_python(parsed_json)
            
            if verdict.verdict == "FIX" and not verdict.antigravity_prompt.evidence_collection:
                if attempt == 0:
                    logger.info("FIX verdict returned empty evidence_collection. Retrying once...")
                    continue
                else:
                    return FixVerdict(
                        verdict="FIX",
                        summary="Review failed due to malformed output.",
                        findings=[
                            {
                                "severity": "blocker",
                                "category": "correctness",
                                "file": "system",
                                "line": 0,
                                "description": "Reviewer output was malformed — the reviewer did not include evidence collection commands. Retry the upload.",
                                "why_it_matters": "Tumbler cannot proceed without actionable evidence collection commands."
                            }
                        ],
                        antigravity_prompt={
                            "objective": "Retry the review.",
                            "constraints": [],
                            "acceptance_criteria": [],
                            "evidence_collection": []
                        }
                    )
            
            return verdict
            
        except Exception as e:
            logger.exception("Provider error or validation failed.")
            if attempt == 0:
                continue
            else:
                raise e
    raise RuntimeError("Review failed unexpectedly.")
