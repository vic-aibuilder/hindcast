# Deploy

**Stack:** Netlify (frontend) · Railway (backend). Decided 2026-06-16.

The repo is pre-configured; the steps below are the per-host dashboard setup.

## Backend → Railway (FastAPI)

1. New Railway project → **Deploy from GitHub repo** → `vic-aibuilder/hindcast`.
2. **Root directory:** repo root (`/`). Railway/nixpacks detects Python from `requirements.txt` and pins 3.12 via `.python-version`.
3. **Start command** comes from the `Procfile`: `uvicorn api:app --host 0.0.0.0 --port $PORT` (Railway injects `$PORT`).
4. **Environment variables:**
   - `ANTHROPIC_API_KEY`
   - `TAVILY_API_KEY`
   - `ALLOWED_ORIGINS` = the Netlify URL (e.g. `https://hindcast.netlify.app`)
   - `DB_PATH` = `/data/hindcast.db` (persistent volume — see "Database & seeding")
5. **Attach a volume** mounted at `/data` (Railway → service → Volumes) so the DB survives redeploys.
6. Note the generated service URL (e.g. `https://hindcast-api.up.railway.app`).

> ⚠️ **#54 is fixed** (`/query` no longer blocks the event loop), so Railway's health check won't freeze the server mid-query.

## Frontend → Netlify (Vite/React)

1. New Netlify site → **Import from GitHub** → `vic-aibuilder/hindcast`.
2. Build settings come from `netlify.toml` (base `frontend`, `npm run build`, publish `dist`).
3. **Environment variable:**
   - `VITE_API_URL` = the Railway backend URL from step 6 above.
4. Redeploy after setting `VITE_API_URL` (it's baked in at build time).

## Database & seeding (critical — do not skip)

`hindcast.db` is **gitignored**, so the container deploys with an **empty** database. Synthesis needs the seed corpus, so the DB must be seeded once, and it must persist:

1. **Persist it:** set `DB_PATH=/data/hindcast.db` and attach a Railway volume at `/data` (above). Without a volume the DB resets on every redeploy.
2. **Seed it once** (after the volume is attached and keys are set) — from the Railway service shell:
   ```
   python -m corpus.seed_loader
   ```
   Loads the seed images and extracts their schemas via Claude (~100+ vision calls, serial — a few minutes, one-time). Idempotent — already-extracted images are skipped, so reruns are quick.
3. With the volume attached, redeploys keep the seeded data — no re-seeding needed.

## After both are up

- Confirm the Netlify origin is in the backend's `ALLOWED_ORIGINS` (CORS), and `VITE_API_URL` points at Railway.
- Smoke test: load the Netlify site, submit a brief, confirm a result renders.
- **Pre-warm the demo brief** against the deployed backend **after** seeding, so the rehearsal run is a fast cache hit.
