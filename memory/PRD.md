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
- **Design**: Monochrome + Copper (#C47C3C / #E2A76F) premium palette

## What's Been Implemented

### Этап 1 (MVP) — 2026-03-01
- All core pages (28+) in RU/DE
- Full SEO package
- Lead form with MongoDB
- Analytics tracking

### v2 Audit & Polish — 2026-03-01
- [x] **Design System v2**: Copper/Monochrome palette (removed cyan/teal)
- [x] **DE Umlauts**: All German text uses proper ü ä ö ß (not ue ae oe ss)
- [x] **OG Image**: Generated and connected to all pages via og:image meta
- [x] **Lead Form Enhanced**: UTM params (source/medium/campaign/content/term), page_url, referrer, lead_type
- [x] **Fluid Typography**: clamp() for H1/H2
- [x] **CSS Variables**: Centralized color control via :root variables
- [x] **Accessibility**: aria-labels on CTAs, focus-visible states
- [x] **Consent**: DSGVO-compliant (analytics OFF by default for DE)
- [x] **Forms.js**: UTM capture from URL, referrer tracking
- [x] **SEO verified**: canonical, hreflang, x-default, schemas, OG on all pages

### Testing Results
- v1: 100% backend, 95% frontend
- v2: 98.7% backend, 100% frontend, 99.4% overall

## Prioritized Backlog

### P0 (Next)
- [ ] Connect real NextBot widget (NEXTBOT_REF_URL in .env)
- [ ] Connect real Telegram bot URL (TELEGRAM_CTA_URL in .env)
- [ ] Add GA4 + Meta Pixel IDs (GA4_ID, META_PIXEL_ID in .env)
- [ ] Email/Telegram notifications on new leads (TELEGRAM_WEBHOOK / SMTP in .env)

### P1 (Этап 2)
- [ ] 5 remaining niche detail pages (clinic, auto, food, real-estate, retail)
- [ ] Cases page with real/anonymous case studies
- [ ] 10+ more blog articles (outlines ready)
- [ ] Blog category filtering
- [ ] A/B testing for CTA copy

### P2 (Backlog)
- [ ] Multi-step lead qualification wizard
- [ ] Blog search
- [ ] Custom OG images per page/language
- [ ] Performance audit (Core Web Vitals)

## File Structure
```
/app/backend/
  server.py           # FastAPI SSR app
  config.py           # Central ENV config
  content/
    __init__.py, ru.py, de.py, blog.py
  templates/
    base.html, partials/, page templates
  static/
    css/style.css, js/main.js|forms.js|consent.js|track.js
/app/frontend/
  server.js           # Express proxy
  tailwind.config.js  # Copper palette
  src/input.css       # Tailwind components
```
