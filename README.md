# Tumbler
### *Clean-State Codebase Auditor and Gatekeeper*

![Tumbler Dashboard](evidence/main-page.png)

Tumbler is a local development gatekeeper and codebase auditor designed to enforce strict code hygiene, test verification, and secret scanning before you build new features. By analyzing a repository's source files, test logs, and visual screenshots, it returns a binary verdict: **PASS** (codebase is clean and ready to extend) or **FIX** (codebase has blockers, accompanied by a drop-in Antigravity prompt to resolve them).

As an extension of its workflow, Tumbler interfaces with [Crucible](https://github.com/OmarAK-Git/crucible) via a one-way file handoff, allowing developers to push verified codebases directly into Crucible's adversarial prompt-hardening engine.

---

## 1. What is Tumbler?

### The One-Sentence Thesis
Tumbler acts as an idea incubator and compliance gatekeeper, ensuring your current codebase is clean, tested, and secure *before* you initiate chat sessions or invoke agentic coding platforms to build new features.

### The Pipeline Diagram
```
                     [ Local Codebase Folder ]
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   Bundler & Filters   │  (Regex scan + XML build)
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   Gemini 1.5 Pro      │  (Verifies evidence & code)
                     └───────────┬───────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
         ┌──────────────┐                ┌──────────────┐
         │ FIX Verdict  │                │ PASS Verdict │
         │ (Get Prompt) │                │ (Ship Code)  │
         └──────────────┘                └───────┬──────┘
                                                 │
                                                 ▼ (Optional Push)
                                         ┌──────────────┐
                                         │  CRUCIBLE    │  <-- Extension
                                         │ (Handoff)    │
                                         └──────────────┘
```

### Why Tumbler Exists
When building applications using agentic workflows (vibecoding), developers often run into a common failure mode: **building on top of broken foundations**. 
If your codebase has unhandled warnings, missing tests, hardcoded credentials, or failing builds, adding a new feature will cause the AI agent to write conflicting code, get stuck in debugging loops, and burn tokens.

Tumbler solves this by acting as a manual quality gate. It verifies that:
1. **Your tests are green** (by requiring and parsing an actual test log file).
2. **Your UI is validated** (by checking for visual screenshot evidence of the running app).
3. **Your secrets are clean** (via a fast local regex secret pre-filter).
4. **Your dependencies are safe** (by auditing requirements files).

---

## 2. Design Decisions

### A. Why Gemini 1.5 Pro
Tumbler uses Google's Gemini 1.5 Pro model for its core auditing logic.
* **Massive Context Window:** Gemini easily ingests entire repository structures, source files, and log dumps simultaneously.
* **Multimodal Reasoning:** Gemini reviews screenshot files in the `evidence/` directory to visually verify that the application matches its design descriptions.
* **GCP IAM Integration:** Developers authenticate locally using native Application Default Credentials (ADC), bypassing the need to manage API keys.

### B. Codebase as a Structured XML Corpus
Before calling the LLM, Tumbler packages all codebase files into a single structured XML document. It recursively walks the project directory, extracts text, skips binaries and `.gitignore` paths, and wraps each file in explicit `<evidence>` tags:
```xml
<evidence path="backend/main.py">
# Code content here...
</evidence>
```
This ensures the model sees a clean, structured representation of the entire workspace layout and content.

### C. Binary PASS vs. FIX Verdicts
Tumbler rejects ambiguous or soft warnings. It returns exactly one of two states:
* **PASS:** The codebase matches all specifications, contains no secrets, has passing test files, and contains visual screenshot evidence.
* **FIX:** The codebase contains a security risk, structural bug, or missing compliance files. The review stops, and the developer receives an Antigravity prompt designed to resolve the specific findings.

### D. Evidence-Based Auditing (The "Double-Lock" Principle)
A developer cannot "trick" Tumbler into giving a PASS. A PASS verdict strictly requires:
1. **Test Verification:** A test run log (e.g. `evidence/test-results.txt` showing zero failures).
2. **Visual Verification:** At least one PNG screenshot in the `evidence/` folder showing the application interface.

If either file is missing or contains failures, Tumbler returns a `FIX` verdict.

### E. The Disagreement Flow
If Tumbler returns a `PASS` but the developer discovers a bug or disagrees with the review, they can challenge the model. By committing a file at `/evidence/disagreement/[note].md` explaining the issue, the developer forces Tumbler to parse the challenge on the next run. Tumbler will transition to a `FIX` verdict and output a remediation prompt targeting the challenge description.

### F. Ephemeral Local Design
Tumbler is designed to run locally and ephemerally:
* **No Database:** Sessions are handled in memory.
* **No External RAG:** The entire codebase is loaded directly into the context window for precise, exhaustive reasoning.
* **No Code Modification:** Tumbler never edits your code; it only audits and advises.

### G. Crucible Integration (The Handoff Extension)
When a codebase achieves a `PASS` verdict, Tumbler exposes a `"Push to Crucible"` toggle. When clicked, it packages the XML corpus and writes a JSON handoff to `~/.crucible/incoming/`. This enables a clean, one-way handoff to Crucible's prompt-hardening loop without making Crucible a dependency of Tumbler.

---

## 3. Architecture

Tumbler's backend is a Python FastAPI app paired with a clean HTML/JS frontend.

```
                    ┌────────────────────────┐
                    │      FastAPI App       │
                    │    (backend/main.py)   │
                    └───────────┬────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Corpus Extractor │  │ Secret Pre-Filter│  │ Crucible Handoff │
│(backend/extract.y)│  │ (backend/main.py)│  │(crucible_handoff)│
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

### Module Walkthrough
* **`backend/extract.py`:** Recursively inspects the repository, respects `.gitignore`, reads files, and bundles them into the structured XML corpus.
* **`backend/main.py`:** Main API definition. Implements the `/api/review` endpoint, performs the local regex secret scanning pre-filter, calls Gemini 1.5 Pro, and manages active session states.
* **`backend/crucible_handoff.py`:** Manages the handoff directory creation, maps the schema, and exports the JSON payload to `~/.crucible/incoming/`.

---

## 4. Proof of Concept (Test Evidence)

Below are three examples of Tumbler running on real codebases:

### 1. The Tumbler-on-Tumbler Self-Review (PASS)
* **What we tested:** We ran Tumbler on its own repository to ensure the project passes its own gate.
* **The Evidence (Console Output):**
```text
Collected 47 files for review.
Extracting and reading files...
Running Tumbler-on-Tumbler review...

=== TUMBLER-ON-TUMBLER REVIEW VERDICT ===
Verdict: PASS
Summary: This project successfully scanned its own repository, verified the presence of the test suite (10 passed tests), confirmed dependency vulnerability scans had zero findings, and reviewed the visual evidence. All compliance gates are satisfied.
```
* **What it demonstrates:** This proves that the codebase matches all its own hygiene standards, including passing pytest logs and screenshot evidence.

---

### 2. Secret Scanning Gating (FIX)
* **What we tested:** A codebase containing a hardcoded AWS key was submitted for review.
* **The Evidence (Pre-filter Block):**
```text
=== VERDICT: FIX ===
Blocker Findings:
1. [blocker] backend/test_app.py:23 - Hardcoded secret detected: aws_access_key. The secret value has been redacted from the reviewer's view, but remains in your source code.

Antigravity Remediation Prompt:
"Your codebase contains a hardcoded AWS secret key at backend/test_app.py:23. Remove the hardcoded secret value, refactor the application to read the credentials from environment variables using os.getenv, and update the setup documentation in the README."
```
* **What it demonstrates:** The local regex pre-filter scans file contents before sending them to the LLM. It blocks the audit, returns a `FIX` verdict immediately, and provides a prompt to extract the secret to an environment variable.

---

### 3. Disagreement Challenge Scenario (FIX)
* **What we tested:** A project had a `PASS` verdict, but a developer created `evidence/disagreement/missing_error_handling.md` pointing out a missing validation block.
* **The Evidence (Remediation prompt generated):**
```text
=== VERDICT: FIX ===
Blocker Findings:
1. [blocker] Developer Challenge (evidence/disagreement/missing_error_handling.md): The app lacks validation on the user registration form, allowing empty submissions.

Antigravity Remediation Prompt:
"Implement validation constraints on the user registration form in frontend/register.html to prevent empty fields. Ensure that the backend API endpoint validates input schemas and returns a 400 Bad Request on empty username or password."
```
* **What it demonstrates:** Tumbler reads files in `/evidence/disagreement/`. If present, it overrides any PASS logic, flags the developer's challenge as a blocker, and outputs the drop-in prompt to implement the fix.

---

## 5. Crucible Integration Handoff

Tumbler includes a file-based handoff extension to bridge codebase audits with feature prompt hardening:

1. **Verify PASS:** Once a codebase receives a clean `PASS` verdict, the UI checkbox **"Push to Crucible after review"** becomes active.
2. **Push Request:** Clicking "Push" calls `/api/sessions/{id}/push-to-crucible`.
3. **Emit File:** The handler writes a JSON bundle to the shared local folder `~/.crucible/incoming/<session_id>.json`:
```json
{
  "tumbler_session_id": "56944127-b582-4390-ad72-75ffb2a0b473",
  "created_at": "2026-05-23T23:49:03.665821+00:00",
  "corpus_bundle": "<EVIDENCE_XML_CONTAINING_GROUNDED_CODE>",
  "source": "tumbler",
  "tumbler_verdict": "PASS"
}
```
Crucible imports this file, allowing the user to initiate adversarial prompt-hardening sessions immediately.

---

## 6. Quick Start

### Prerequisites
* Python 3.11+
* Google Cloud SDK (authenticated with Application Default Credentials)

### 1. GCP Project Setup
Ensure your local environment is authenticated to GCP:
```bash
gcloud auth application-default login
```

### 2. Installation
Clone the repository and set up a virtual environment:
```bash
git clone https://github.com/OmarAK-Git/tumbler.git
cd tumbler
python -m venv .venv
source .venv/Scripts/activate  # On Windows
# source .venv/bin/activate    # On Unix/macOS
pip install -r backend/requirements.txt
```

### 3. Configuration
Copy `.env.example` to `.env` and set your GCP Project ID:
```env
GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
```

### 4. Running the App
Start the backend server using Uvicorn:
```bash
python -m uvicorn backend.main:app --reload
```
Open a browser and navigate to `http://localhost:8000`. Drag and drop any local folder to start auditing.

---

## 7. Status and Roadmap

### V1 — Complete
* [x] Project extraction and XML structured corpus bundling.
* [x] Regex pre-filter secret scanning.
* [x] Vertex AI Gemini 1.5 Pro auditing adapter.
* [x] Compliance evidence check (pytest logs + screenshots).
* [x] Disagreement / developer challenge flow.
* [x] Crucible handoff file emitter (`~/.crucible/incoming/`).

### V2 Backlog
* **Continuous watch mode:** Run Tumbler as a local CLI daemon that watches file changes and automatically triggers audits on save.
* **Expanded pre-filter heuristics:** Add security heuristics to flag insecure configurations (e.g. CORS wildcards, debug mode flags) locally before calling the LLM.
* **Automated prompt generation for Crucible:** Add a feature request text box where the developer types an idea, and Tumbler uses the codebase context to pre-generate a specific draft prompt for the Crucible debate loop.

---

## 8. Inspiration and Credit
* **Vibecoding Paradigm:** Built using the agentic code assembly model.
* **Crucible:** Companion prompt-hardening engine that acts as the next step in the pipeline.
