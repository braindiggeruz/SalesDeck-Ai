# SalesDesk AI · Production Deployment (Cloudflare in front of FastAPI backend)

> **Important:** SalesDesk AI is a **server-rendered FastAPI + Jinja2 + MongoDB** app. Cloudflare Pages **cannot host Python or MongoDB**. The correct production architecture is to keep the backend on its current host (Emergent / Railway / Fly.io / VPS / equivalent) and use **Cloudflare in front as DNS + reverse proxy + SSL/CDN/WAF**. This file documents that path.

---

## Architecture

```
[browser] ──https──▶ [Cloudflare edge: sales-desk.uz]
                          │  proxied (orange cloud)
                          ▼
                    [Origin: FastAPI backend host]
                          │
                          ▼
                       [MongoDB]
```

- All HTML, `/api/lead`, `/api/telegram/webhook`, static assets, `sitemap.xml`, `robots.txt` are served by FastAPI.
- Cloudflare provides: TLS, HTTP/3, caching of static assets, basic DDoS, WAF rules, redirect rules (`www → apex`).
- GA4, Meta Pixel, Telegram bot are unchanged.

---

## DNS plan (after Cloudflare zone is active)

| Type  | Name              | Target / Content                          | Proxy | Notes                                           |
|-------|-------------------|--------------------------------------------|-------|-------------------------------------------------|
| A     | `sales-desk.uz`   | *(IP of the FastAPI backend host)*         | 🟧 ON | Replace placeholder `195.210.46.115`            |
| CNAME | `www`             | `sales-desk.uz`                            | 🟧 ON | `www → apex` (redirect rule does the rewrite)   |
| TXT   | `sales-desk.uz`   | `google-site-verification=…` *(existing)*  | n/a   | **Preserve — Google Search Console**            |
| CNAME | `67atbjgfs7ly`    | `gv-…dv.googlehosted.com` *(existing)*     | ⬜ OFF | **Preserve — Google site verification**         |
| MX / SPF / DKIM / DMARC | (if any) | (existing)                                 | n/a   | **Preserve — do not touch mail records**        |

> Use `proxied=true` (orange cloud) only on records that point to your origin web app. Verification, mail and any TXT/CNAME control records stay DNS-only (grey cloud).

### Cloudflare Redirect Rule (canonical apex)
- **Rule:** when `Hostname == www.sales-desk.uz` → **301** to `https://sales-desk.uz${URI}`.
- Or use a Bulk Redirect List, or a Page Rule (legacy). All three are fine.

### SSL/TLS
- Mode: **Full (strict)** if origin already has a valid cert; otherwise **Full** until origin cert is fixed.
- Always Use HTTPS: **ON**.
- Automatic HTTPS Rewrites: **ON**.

---

## Step-by-step deployment

### A. Cloudflare zone creation (one-time, manual until token has the right scope)
The supplied API token (`cfut_…`) lacks `com.cloudflare.api.account.zone.create`. Either:

**Option 1 — manual via dashboard (5 minutes):**
1. Cloudflare dashboard → **Add a site** → enter `sales-desk.uz` → **Free** plan.
2. Cloudflare will scan existing PS Cloud records. **Do not let it auto-import anything you don't recognise.** Keep only:
   - the existing `A sales-desk.uz` (placeholder for now — will be replaced with the real backend IP)
   - `CNAME www → sales-desk.uz`
   - the Google verification `TXT` and `CNAME 67atbjgfs7ly`
   - any mail records (MX/SPF/DKIM/DMARC) if you have email on this domain.
3. Cloudflare displays two name servers, e.g. `xxx.ns.cloudflare.com` and `yyy.ns.cloudflare.com`.

**Option 2 — re-issue the token with permissions, then re-run automation:**
- Required token permissions (least-privilege):
  - `Account › Zone › Edit` — to create/edit zones in this account.
  - `Zone › DNS › Edit` (after zone exists) — to manage records.
  - `Zone › Zone Settings › Edit` — to set SSL/redirect/HTTPS settings.
  - *(Pages is **not** needed here — we don't deploy to Pages.)*
- Re-run the automation step that creates the zone via `POST /zones` and reads the returned `name_servers`.

### B. Change name servers at PS Cloud (one-time, manual)
In the PS Cloud domain control panel for `sales-desk.uz`:
- Replace `ns1.pscloud.uz` and `ns2.pscloud.uz` with the **two Cloudflare nameservers** shown in step A.
- Save. Activation typically takes minutes; up to 24 hours in the worst case.
- Cloudflare zone will switch from *Pending Nameserver Update* to **Active** automatically.

### C. After zone is Active
1. **Update the apex `A` record** in Cloudflare DNS to point to the FastAPI backend public IP (or `CNAME` to its hostname). Toggle proxy **ON** (orange cloud).
2. **Verify `CNAME www`** is present and proxied.
3. **Add Redirect Rule** `www → apex` (see DNS plan above).
4. **SSL/TLS → Full (strict)**, **Always Use HTTPS = ON**.
5. **Backend env** must have `SITE_URL=https://sales-desk.uz` so canonical, hreflang, sitemap and OG tags render correctly. Restart backend.
6. **Re-deploy the Telegram callback webhook to the new domain**:
   ```
   curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
        -d "url=https://sales-desk.uz/api/telegram/webhook" \
        -d "secret_token=$TELEGRAM_WEBHOOK_SECRET" \
        -d 'allowed_updates=["callback_query"]'
   ```

### D. Verification checklist
- `https://sales-desk.uz/` → 200, HTML renders, no mixed-content warnings.
- `https://www.sales-desk.uz/` → 301 → `https://sales-desk.uz/`.
- `https://sales-desk.uz/sitemap.xml` → XML lists URLs with `https://sales-desk.uz/...`.
- `https://sales-desk.uz/robots.txt` → 200, contains `Sitemap: https://sales-desk.uz/sitemap.xml`.
- `view-source: https://sales-desk.uz/ru/` → contains `<link rel="canonical" href="https://sales-desk.uz/ru/">` and the GA4 + Pixel attributes.
- `https://sales-desk.uz/api/health` → `{"status":"ok"}`.
- Submit `/ru/contact/` form → 200 → Telegram card lands in the group.
- Click ✅ Обработано in Telegram → card edits → Mongo `leads.status == "processed"`.
- Google Search Console → property still verified (TXT and CNAME preserved).

---

## Why **not** Cloudflare Pages

- **Python is not supported.** Pages Functions run V8 (JavaScript/TypeScript only).
- **MongoDB is not supported.** No long-lived TCP from Workers/Pages.
- **Jinja2 SSR has no equivalent on Pages without a full rewrite.**
- Migrating to Cloudflare = full rewrite (Next.js + a JS Mongo replacement or external DB API). Out of scope and not required: the proxy approach gives you the same edge benefits with zero rewrite.

---

## GitHub repo notes
- **Branch:** `main` (production).
- **Build:** none required for the backend image (FastAPI runs from source). For Tailwind CSS rebuild before deploy:
  ```
  cd frontend && yarn tailwindcss -i ./src/input.css -o ../backend/static/css/style.css --minify
  ```
- **Secrets:** `.env` is in `.gitignore` (`*.env`, `*.env.*`). `backend/.env.example` is committed with names only.

---

## Manual security reminders
- Rotate / revoke the temporary Cloudflare API token (`cfut_…`) once the zone is active and the token is no longer needed.
- Rotate `TELEGRAM_WEBHOOK_SECRET` to a strong value before going live and re-call `setWebhook`.
- Keep `TELEGRAM_BOT_TOKEN`, `MONGO_URL`, `TELEGRAM_WEBHOOK_SECRET` only on the backend host — never in any frontend bundle, public env, or repository.
