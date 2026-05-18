# Tumbler

Tumbler is a local web app that takes a folder of your code and returns exactly one of two verdicts: PASS (done, no blind spots, ship it) or FIX (here is what is wrong, and here is the exact prompt to paste into Antigravity to fix it). It acts as an idea incubator, letting you drop a half-formed project into it to ensure it is developing correctly without getting bogged down by state in your chat sessions.

## Setup

Tumbler requires Python 3.11+.

1. **Create and activate a virtual environment:**
   - **Windows PowerShell:**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **macOS/Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

2. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **GCP Project Setup (for Vertex AI Gemini):**
   - Authenticate with your Google Cloud account:
     ```bash
     gcloud auth application-default login
     ```
   - Copy `.env.example` to `.env` and set your GCP Project ID:
     ```bash
     cp .env.example .env
     ```
     Open `.env` and ensure `GOOGLE_CLOUD_PROJECT=your-project-id` is set.

## Running Locally

From the repository root, start the backend server:

```bash
uvicorn backend.main:app --reload
```

The app is now running. Open your browser and navigate to `http://127.0.0.1:8000`.

## The Workflow

The core Tumbler loop takes three steps. First, you drag your project folder into the web UI and receive a verdict. Second, if you get a FIX verdict, you click the copy button to grab the provided Antigravity Prompt, paste it into Antigravity, and let it implement the fixes. Finally, after Antigravity finishes, you re-upload the folder to verify the changes and continue until you reach a PASS.

## Challenging a PASS

Tumbler expects you to provide evidence. If Tumbler gives you a PASS and you disagree or want to challenge the methodology, create a file at `/evidence/disagreement/[note].md` inside your project and add your note or screenshot there. Re-upload the project, and Tumbler will review your challenge.

## What Tumbler Does NOT Do

Tumbler is deliberately small. In V1, it explicitly does not:
- Edit your code.
- Run your code, tests, or builds.
- Store your code on a server (it's completely local and ephemeral).
- Have a chat interface for follow-up questions.
- Host multiple LLMs debating.
- Use a RAG layer for knowledge (methodology is inline).
- Support user accounts.

## Known Limitations

- **Secret Scanning:** Tumbler's pre-filter regex catches only the most common secret patterns (AWS, GitHub tokens, JWTs). It is not a complete SAST tool.
- **Security Checks:** The reviewer detects obvious, surface-level security issues (e.g., SQL injection, command injection) that are discernible from code structure. Deep audits, data-flow analysis, and runtime security require other tooling.
