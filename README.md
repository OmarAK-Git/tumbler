# Tumbler

Tumbler is a local web app that reviews vibe-coded projects. You upload a folder, and Tumbler tells you if it's a PASS (ship it) or FIX (here is what's wrong and the prompt to fix it).

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **GCP Authentication** (for Vertex AI):
   ```bash
   gcloud auth application-default login
   export GCP_PROJECT_ID="your-project-id"
   ```
   *Note: Tumbler uses `google-cloud-aiplatform` which will automatically pick up your Application Default Credentials and project from the environment if `GOOGLE_CLOUD_PROJECT` or `GCP_PROJECT_ID` is set appropriately, or if it's the default project set in gcloud.*

## Running Locally

1. Start the backend:
   ```bash
   uvicorn backend.main:app --reload
   ```
2. Open your browser to `http://localhost:8000`

## Usage

1. Drag and drop a project folder (or a `.zip` archive of the folder) into the drop zone.
2. Click **Review**.
3. Wait up to 60 seconds for the verdict.
4. You will receive a JSON response showing either `PASS` or `FIX`.

## Architecture (Phase 1)

This is Phase 1 (Walking Skeleton):
- It has a minimalistic system prompt.
- Evidence collection and methodology blocks are not yet implemented.
- The UI outputs raw JSON.
- Uploaded files are extracted to a temporary directory, read, sent to Vertex AI Gemini, and then completely deleted. No persistence.
