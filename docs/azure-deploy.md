# Azure deployment (backend + frontend as code, Neon database)

Two App Services, both Linux, plan B1 or higher:

| App | Stack | Branch | Workflow |
|---|---|---|---|
| `idara-tunisie` (backend) | Python 3.12 | `main` | `.github/workflows/deploy-azure.yml` |
| `idara-tunisia` (frontend) | Node 22 LTS | `frontend` | `deploy-frontend.yml` on that branch |

## Backend (`idara-tunisie`)

1. **Neon**: project with `CREATE EXTENSION IF NOT EXISTS vector;`, copy the connection string.
2. **Environment variables** (Settings > Environment variables):
   - `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
   - `WEBSITES_PORT=8000`
   - `DATABASE_URL=<Neon connection string>`
   - `RUNTIME_ENV=dev` (`prd` additionally requires `JWT_VERIFICATION_KEY`)
   - `AUTH_JWT_SECRET=<long random string>` (login tokens; the app refuses to start without it in `prd`)
   - `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` (OpenAI-compatible chat gateway)
   - `TMAPS_API_KEY` (places search)
   - `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `ADZUNA_COUNTRY` (job offers)
3. **Startup command** (Settings > Configuration > General settings):
   `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   and set **Startup timeout** (`WEBSITES_CONTAINER_START_TIME_LIMIT`) to `600`: the first start downloads the
   embeddings model (~220 MB, `paraphrase-multilingual-MiniLM-L12-v2`) and indexes the knowledge bases.
4. **GitHub**: App Service > *Download publish profile* > repo secret `AZURE_WEBAPP_PUBLISH_PROFILE`.
   If it is missing, enable Settings > Configuration > *SCM Basic Auth Publishing Credentials*.
5. Push to `main` (or run the workflow manually). Check `https://<backend>.azurewebsites.net/docs`.

## Frontend (`idara-tunisia`)

1. **Environment variables**: `BACKEND_URL=https://<backend>.azurewebsites.net` (the Node server proxies `/api/*`
   to it, with a 180 s timeout, which the CV analysis and agent answers need).
2. **GitHub**: download this app's publish profile into the repo secret `AZURE_WEBAPP_PUBLISH_PROFILE_FRONTEND`.
3. Push the Angular project to the `frontend` branch (it also carries `server.js` and the workflow).

## Notes

- Embeddings run locally on CPU (no API). The vector tables live in `tmp/lancedb`, which is not deployed: the
  server rebuilds them at startup, in the background.
- Stop/start: both apps are billed while running. Use *Stop* in the portal when not demoing.
