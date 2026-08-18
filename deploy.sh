# Deploy to Cloud Run (scales-to-zero → near-zero idle cost).
# Meets the hackathon's "Google Cloud infrastructure service" requirement
# alongside Firestore (optional mirror in memory.py).

# 1. Build + push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/knotulus-lite --region $REGION

# 2. Deploy (min-instances 0 = scale to zero)
gcloud run deploy knotulus-lite \
  --image gcr.io/$PROJECT_ID/knotulus-lite \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 2 \
  --set-env-vars ENABLE_GEMINI=$ENABLE_GEMINI,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GEMINI_MODEL=gemini-3.5-flash

# 3. Authenticate ADC once (no API key needed):
#    gcloud auth application-default login
