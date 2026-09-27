# Azure deployment (backend as code + Neon database)

1. **Neon**: create a project, run `CREATE EXTENSION IF NOT EXISTS vector;`, copy the connection string
   (`postgresql://user:pass@host/db?sslmode=require`).
2. **App Service**: Create > Web App > Publish: **Code**, Runtime stack: **Python 3.12**, OS: Linux,
   region France Central, plan B1 (F1 is too small for this app).
3. **Environment variables** (Settings > Environment variables):
   - `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
   - `WEBSITES_PORT=8000`
   - `DATABASE_URL=<Neon connection string>`
   - `RUNTIME_ENV=dev` for a first test (`prd` requires `JWT_VERIFICATION_KEY`)
   - `GROQ_API_KEY`, `OPENAI_API_KEY`, `VOYAGE_API_KEY`, `TMAPS_API_KEY`
4. **Startup command** (Settings > Configuration > General settings):
   `uvicorn app.main:app --host 0.0.0.0 --port 8000`
5. **GitHub**: App Service > Overview > *Download publish profile*; add its content as the repo secret
   `AZURE_WEBAPP_PUBLISH_PROFILE`. If it is missing, enable Settings > Configuration >
   *SCM Basic Auth Publishing Credentials*. Push to `main` to deploy.
6. Check `https://<app>.azurewebsites.net/docs`.
