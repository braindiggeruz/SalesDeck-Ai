# SalesDesk AI — PRD & Progress

## Problem Statement
SEO-optimized multilingual (RU/DE) website for SalesDesk AI brand — AI Sales Bot 24/7 integrator. 
Goal: convert traffic (Meta Ads + organic) into NextBot referral signups and turnkey implementation requests.

## Architecture
- **Backend**: FastAPI + Jinja2 SSR (port 8001) — all HTML rendered server-side
- **Frontend**: Express.js proxy (port 3000) → forwards to FastAPI
- **CSS**: Tailwind CLI build (minified, no CDN)
- **DB**: MongoDB (leads collection)
- **i18n**: RU + DE with URL prefix structure (/ru/*, /de/*)

## User Personas
1. **SMB Owner (Uzbekistan)** — needs AI sales bot, wants turnkey implementation (RU)
2. **SMB Owner (Germany/Europe)** — same need, German-speaking (DE)
3. **DIY User** — wants to self-serve register via NextBot referral link

## Core Requirements (Static)
- SSR/SSG for SEO (no SPA render)
- hreflang + canonical + sitemap + robots.txt
- JSON-LD schemas (Organization, WebSite, BreadcrumbList, FAQPage, Article, SoftwareApplication)
- Progressive forms (HTML works without JS, fetch as enhancement)
- Honeypot + rate limit anti-spam
- GDPR consent banner (analytics only after consent)
- All config via ENV (no hardcoded keys)

## What's Been Implemented (2026-03-01)

### Этап 1 (MVP) — COMPLETE
- [x] Language chooser (/) — 200 OK, x-default
- [x] Home RU + DE (hero, problems, solution, industries, stats, process, guarantee, FAQ)
- [x] Solutions index RU + DE (7 niches listed)
- [x] Solution detail pages: beauty + education (RU + DE)
- [x] Pricing RU + DE (4 packages: Self-Serve, Lite, Pro, Max)
- [x] Demo RU + DE (widget placeholder + Telegram fallback + tips + FAQ)
- [x] Blog index + 2 articles RU + 2 articles DE
- [x] About RU + DE
- [x] Contact RU + DE (progressive form with honeypot)
- [x] Privacy + Terms (RU + DE)
- [x] Cases placeholder (RU + DE)
- [x] 404 page with language detection
- [x] Full SEO package (title, desc, canonical, hreflang, OG, schemas)
- [x] sitemap.xml (all pages + hreflang)
- [x] robots.txt
- [x] Breadcrumbs on all inner pages
- [x] Cookie consent banner (analytics only after consent)
- [x] Event tracking helper (track function)
- [x] /api/lead POST endpoint (MongoDB, rate limited, honeypot, validation)
- [x] Tailwind CLI build (minified CSS, no CDN)
- [x] All config via ENV (.env files)

### Testing: 100% backend, 95% frontend

## Prioritized Backlog

### P0 (Next)
- [ ] Connect real NextBot widget (async/defer, CLS-safe)
- [ ] Connect real Telegram bot URL
- [ ] Add GA4 + Meta Pixel IDs

### P1 (Этап 2)
- [ ] 5 remaining niche pages (clinic, auto, food, real-estate, retail)
- [ ] Cases page with real/anonymous case studies
- [ ] More blog articles (12 RU + 12 DE outlines ready)
- [ ] OG images generation

### P2 (Backlog)
- [ ] Email notification on lead submission (SendGrid/SMTP)
- [ ] Telegram webhook for lead notifications
- [ ] A/B testing for CTA copy
- [ ] Blog categories/tags filtering
- [ ] Blog search
- [ ] Multi-step lead qualification form

## File Structure
```
/app/backend/
  server.py           # FastAPI SSR app (all routes)
  config.py           # Central ENV config
  content/
    __init__.py       # Content loader
    ru.py             # All RU content
    de.py             # All DE content
    blog.py           # Blog articles data
  templates/
    base.html         # Base layout (head, SEO, scripts)
    partials/         # header, footer, consent, cta_block
    home.html, pricing.html, demo.html, etc.
  static/
    css/style.css     # Built Tailwind CSS
    js/               # main.js, forms.js, consent.js, track.js
/app/frontend/
  server.js           # Express proxy to FastAPI
  tailwind.config.js  # Tailwind config
  src/input.css       # Tailwind source
```
