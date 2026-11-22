# Deploy environment note

`/opt/gymmolly/.env` on the server is the single, server-owned source of runtime configuration.
Docker Compose reads it for `${VAR}` substitution into the backend service.

- CI (`.github/workflows/deploy.yml`) no longer copies any env file over it, so edits persist across deploys.
- `deploy.sh` excludes env files from the package and the rsync, and does not create `.env`.
- `backend/.dockerignore` keeps `.env*` out of the backend image.
- This repo is public. Never commit env files or values. `.env.example` lists variable names only.
- Email: set `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_EMAIL_API_TOKEN` in the server `.env` to send via Cloudflare.
  If either is missing, the app falls back to SendGrid (`SENDGRID_API_KEY`).
- Total raw attachment size per email is capped at 18 MiB (Cloudflare limits the whole message to 25 MiB with base64).
