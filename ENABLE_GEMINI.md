"""
# ENABLE_GEMINI runbook — switch from mock to real Gemini 3.5 Flash

1. Ensure gcloud is installed and you are logged in:
       gcloud auth application-default login
   (No API key needed — Application Default Credentials is the recommended method.)

2. Set your project:
       gcloud config set project <YOUR_GCP_PROJECT_ID>

3. Create .env (copy from .env.example) and set:
       ENABLE_GEMINI=true
       GOOGLE_CLOUD_PROJECT=<YOUR_GCP_PROJECT_ID>
       GOOGLE_CLOUD_LOCATION=us-central1

4. Run locally:
       . .venv/Scripts/activate
       python -m src.orchestrator          # mock-or-real depending on .env
       uvicorn src.gateway:app --port 8080 # API

5. Deploy to Cloud Run (scales-to-zero):
       ./deploy.sh   (edit PROJECT_ID / REGION / ENABLE_GEMINI first)

The code paths are identical in both modes; only the model backend changes.
"""
