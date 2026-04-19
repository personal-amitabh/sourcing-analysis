# Sourcing Analysis App

Supplier sourcing intelligence dashboard backed by Google Sheets.

## Setup

### 1. Install dependencies
```bash
npm install
```

### 2. Configure environment variables
Copy `.env.local.example` to `.env.local` and fill in all values:

```bash
cp .env.local.example .env.local
```

Required values:
- `NEXT_PUBLIC_APPS_SCRIPT_URL` — Your Google Apps Script Web App URL
- `APPS_SCRIPT_TOKEN` — The secret token set in your Apps Script
- `NEXTAUTH_SECRET` — Run `openssl rand -base64 32` to generate
- `NEXTAUTH_URL` — `http://localhost:3000` for local, your Vercel URL for production
- `GOOGLE_CLIENT_ID` — From Google Cloud Console OAuth credentials
- `GOOGLE_CLIENT_SECRET` — From Google Cloud Console OAuth credentials
- `ALLOWED_USERS` — Comma-separated list of allowed email addresses
- `ANTHROPIC_API_KEY` — Your Anthropic API key from console.anthropic.com

### 3. Run locally
```bash
npm run dev
```

Visit http://localhost:3000

## Deploying to Vercel

1. Push this repo to GitHub
2. Import into Vercel at vercel.com
3. Add all environment variables from `.env.local` in Vercel project settings
4. Update `NEXTAUTH_URL` to your Vercel deployment URL (e.g. `https://sourcing-analysis.vercel.app`)
5. Add your Vercel URL to Google Cloud Console → OAuth Client → Authorized JavaScript Origins
6. Add `https://your-app.vercel.app/api/auth/callback/google` to Authorized Redirect URIs

## Adding New Users
Update the `ALLOWED_USERS` environment variable in Vercel and redeploy.

## Features
- Google OAuth login with allowlist access control
- Summary stats: unique parts, suppliers, single vs multi-sourced breakdown
- Multi-source depth: % of parts with 2, 3, 4+ suppliers
- Searchable, filterable, sortable data table with pagination
- AI-powered part enrichment (on-demand) — writes back to Google Sheet
