# ANTIGRAVITY_KICKOFF.md — Tumbler Phase 1 only

## How to use this file

Copy everything between the `=== PROMPT START ===` and `=== PROMPT END ===` markers below. Paste it into a new Antigravity session. Make sure `SPEC.md` and `IMPLEMENTATION_PLAN.md` are in the project directory before Antigravity reads them — it will need them.

**Critical:** this prompt is scoped to **Phase 1 only**. Do not paste Phase 2 or Phase 3 work into the same Antigravity session. When Phase 1's verification gate passes, start a new Antigravity session with a new prompt for Phase 2 (you can write that prompt yourself or ask Claude for it then — but not now).

---

## === PROMPT START ===

You are helping build Phase 1 of a project called **Tumbler**. Read the two files `SPEC.md` and `IMPLEMENTATION_PLAN.md` in the project root before writing any code. The full context for the project lives in those files. Your work in this session is **strictly scoped to Phase 1** as described in `IMPLEMENTATION_PLAN.md`. Do not implement anything from Phase 2 or Phase 3, even if you think it would be helpful.

### What Tumbler is (short version)

Tumbler is a local web app that reviews vibe-coded projects. The user uploads a folder. Tumbler returns one of two verdicts: PASS (ship it) or FIX (here's what's wrong and here's the exact prompt to fix it in Antigravity). It's the user's idea incubator — a tool that pushes projects forward instead of requiring the user to hold all the state in their head.

### Your task

Build the Phase 1 "Walking Skeleton" exactly as scoped in `IMPLEMENTATION_PLAN.md`. The goal is end-to-end: a user can upload a folder (as a zip) via a web UI, the backend extracts it, sends file contents to Vertex AI Gemini, gets a structured verdict back, and shows the verdict to the user.

### Hard constraints

1. **Stack:** Python 3.11+, FastAPI, `google-cloud-aiplatform` for Vertex AI, `pydantic` for schema validation. Frontend is one static HTML file with vanilla JS. No React, no build step, no bundler.

2. **No Phase 2 or Phase 3 features.** Specifically, do NOT build:
   - Secret pre-filter / regex scanner
   - `<evidence>` block delimiters around file content
   - Styled PASS/FIX UI (the verdict displays as raw JSON in a `<pre>` block for Phase 1)
   - The methodology block in the system prompt
   - Provider abstraction interface (the Vertex AI call is a direct function in Phase 1)
   - Evidence directory convention enforcement in the system prompt

3. **The system prompt for Phase 1 is minimal.** It contains:
   - The reviewer role ("You are a senior engineer reviewing a single application…")
   - The PASS bar (the five conditions from SPEC.md)
   - The exact verdict schema (PASS or FIX)

   That's it. No methodology, no inline OWASP guide, no evidence convention. Phase 2 adds those.

4. **The verdict must be schema-validated.** Use Pydantic. If the LLM returns malformed JSON, the backend catches the parse error and returns a synthetic FIX verdict with one finding: `"reviewer output malformed — please try the upload again"`. The backend never returns a 500 to the user due to LLM output issues.

5. **Temp files must be cleaned up.** Use a `try/finally` (or `tempfile.TemporaryDirectory` context manager) around the extract/read/review flow. After the verdict is returned, no extracted files remain on disk.

6. **No persistence.** Do not write a database. Do not save verdicts to disk. Each review is independent.

### Deliverable file structure

Create exactly this structure:

```
tumbler/
├── backend/
│   ├── main.py              # FastAPI app, /api/review and / routes
│   ├── reviewer.py          # Vertex AI call + minimal system prompt
│   ├── schemas.py           # Pydantic: PassVerdict, FixVerdict, Verdict (discriminated union)
│   ├── extract.py           # Zip extraction + text file reading (skip binaries)
│   └── requirements.txt
├── frontend/
│   └── index.html           # Drag-drop zone, Review button, <pre> for JSON verdict
├── README.md                # Local setup + run instructions
├── SPEC.md                  # (already exists — do not modify)
└── IMPLEMENTATION_PLAN.md   # (already exists — do not modify)
```

### Key implementation notes

**`schemas.py`** — Use Pydantic v2 discriminated union on the `verdict` field. PassVerdict has `verdict: Literal["PASS"]` and a few summary fields. FixVerdict has `verdict: Literal["FIX"]` and a `findings` list plus an `antigravity_prompt` object. Match the schema in SPEC.md exactly — same field names, same types.

**`extract.py`** — Accept an UploadFile. If it's a zip, extract to a temp dir. If it's a folder upload (browser-supplied), reconstruct the structure. Walk the resulting directory. Read each file as UTF-8; if decoding fails, list the filename but don't include content. Return a list of `(relative_path, content_or_none)` tuples. Skip files in common ignore patterns: `.git/`, `node_modules/`, `__pycache__/`, `.venv/`, `dist/`, `build/`.

**`reviewer.py`** — One function: `async def review(files: list[tuple[str, str]]) -> Verdict`. Builds the evidence bundle as a plain string (no `<evidence>` delimiters in Phase 1 — just `=== file: path/to/file.py ===\n<content>\n\n=== file: ... ===\n...`). Calls Vertex AI Gemini via `google-cloud-aiplatform`. The system prompt asks for JSON output matching the verdict schema. Parses the response. On parse failure, returns the synthetic-FIX-verdict described above.

**`main.py`** — FastAPI app. `POST /api/review` accepts a multipart form with the upload, runs extract → review, returns the verdict JSON. `GET /` returns the static `frontend/index.html`. Mount static files appropriately. CORS not needed (single origin).

**`frontend/index.html`** — Drag-and-drop zone (or fall back to a file picker), a Review button, a `<pre>` block for the verdict, a simple loading state ("Reviewing… this can take up to 60 seconds"). Use `fetch()` with `FormData` to POST to `/api/review`. No frameworks. Pure HTML/JS.

**`README.md`** — Install Python deps, run `gcloud auth application-default login`, set `GCP_PROJECT_ID` env var, run `uvicorn backend.main:app --reload`, open `http://localhost:8000`.

### How to verify Phase 1 is done

Before declaring the work complete, run the verification gate from `IMPLEMENTATION_PLAN.md`:

1. Upload a small test folder. Get a JSON verdict back in under 60 seconds.
2. The JSON parses as a valid `PassVerdict` or `FixVerdict`.
3. Plant a hardcoded API key in a test file, upload. Verdict is FIX. (Note: in Phase 1 there is no regex scanner, so this works purely because the LLM notices the secret. That's fine for Phase 1.)
4. Upload a tiny folder with just a README. Verdict is either PASS or FIX — never a server error.
5. After any review, check the OS temp directory. No leftover extracted files from the upload.

If all five pass, Phase 1 is done. **Stop there.** Do not start Phase 2. Tell the user the gate has passed and wait for the next instruction.

### What to do when you have questions

Ask before guessing. Specifically ask if:
- You're tempted to add anything not listed in "Deliverable file structure."
- You think a Phase 2 feature would "just be easier to do now."
- The user's setup (Python version, OS, GCP project) is ambiguous.

Otherwise, proceed.

## === PROMPT END ===

---

## After Phase 1

Once Phase 1's verification gate passes:

1. Commit everything to git. Tag it `v0.1-phase1`.
2. Use Tumbler on itself (upload Tumbler's own backend as a zip). The verdict it produces is your guide for Phase 2 — it'll tell you what's weak.
3. Open a new Antigravity session. Write (or ask for) the Phase 2 prompt using the same pattern as this one. Do not paste Phase 1's prompt into the new session.

The reason Phase 1's UI is intentionally ugly (raw JSON in a `<pre>` block) is so that you can verify the loop works end-to-end without getting distracted by polish. Polish is Phase 2's job.
