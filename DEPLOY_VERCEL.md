# Deploy CV Maker to Vercel

## What is already configured

- `vercel.json` routes all traffic to the FastAPI ASGI app.
- `api/index.py` exposes your existing `app` from `app.py`.

## Required environment variables in Vercel

Add these in **Vercel Project → Settings → Environment Variables**:

- `API_KEY` (required)
- `API_KEY_HEADER` (optional, default is `X-API-Key`)
- `ALLOWED_IPS` (optional, comma-separated)
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` (required for Gemini features)
- `MONGODB_URI` (required)
- `MONGODB_DB` (optional, default `my_info`)
- `MONGODB_COLLECTION` (optional, default `profiles`)
- `APIFY_API_TOKEN` (required if using LinkedIn/Apify extraction)

## Deploy from GitHub (recommended)

1. Push this repository to GitHub.
2. In Vercel, click **Add New Project** and import the repo.
3. Framework preset: **Other**.
4. Root directory: project root.
5. Add the environment variables listed above.
6. Click **Deploy**.

## Deploy from CLI

```bash
npm i -g vercel
vercel login
vercel
```

For production:

```bash
vercel --prod
```

## Verify after deploy

- Open `/health` and confirm `{"status":"ok"}`.
- Open `/docs` and test any protected endpoint using your `API_KEY` header.
- For Gemini endpoints, optionally send `X-Gemini-Api-Key` to override per request.

## Notes

- Vercel serverless functions are stateless and can cold-start.
- Keep MongoDB reachable from Vercel and allow Vercel egress IPs if your DB is IP-restricted.
- For production, restrict CORS origins in `app.py` instead of allowing all origins.
