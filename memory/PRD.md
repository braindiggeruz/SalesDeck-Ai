# SalesDesk AI — Product Requirements & Status

**Stack:** FastAPI + Jinja2 SSR · Tailwind (CLI compile) · MongoDB · Vanilla JS islands. Hosted on Emergent K8s (port 8001 backend / 3000 frontend; ingress maps `/api/*` to 8001).

**Languages:** RU + DE strict path-based routing (`/ru/*`, `/de/*`); root `/` = language chooser (`x-default`).

**Core flow:** Visit → понял боль → увидел выгоду → демо/Telegram/contact → лид в Mongo → менеджер закрывает.

---

## Phases delivered

### Phase 1 — MVP (✅)
SSR site, RU+DE i18n, all pages (Home, Solutions index + 7 niches, Pricing, Demo, Contact, About, Privacy, Terms, Blog, Cases, 404), `/api/lead` with rate-limit + honeypot + UTM/referrer capture, sitemap.xml + robots.txt + schema.org JSON-LD (Organization, WebSite, BreadcrumbList, FAQPage, SoftwareApplication, Article).

### Phase 2 — Design V2 "Copper" (✅)
Premium dark + Copper (#C47C3C) palette via Tailwind config; gradient text; card-hover; glow lines; consent banner; OG image generation (Gemini Nano Banana).

### Phase 3 — CRO Audit (✅, Feb 2026)
Strategic 16-point text-only roadmap delivered to the user.

### Phase 4 — CRO Uplift Batch (✅, Feb 2026 — current)
Implemented in a single autonomous pass:
1. New performance hero: "AI-бот отвечает клиентам за секунды — даже когда менеджер занят" + chat mockup (right column) with status badges.
2. Unified CTA architecture: **Primary** "Получить демо"/"Demo anfordern" → /demo · **Secondary** "Обсудить запуск"/"Implementierung besprechen" → /contact · **Telegram escape link** (text, not button).
3. Trust strip under hero (4 items, no fakes; with footnote about channel availability).
4. "Сколько стоит медленный ответ?" / "Was kostet eine langsame Antwort?" cost-of-inaction block (3 cards).
5. Flow timeline: 4 steps (User → AI → AI → Team) with role-coloured tags.
6. **Pricing reordered:** Lite → **Pro (Рекомендуем/Empfohlen)** → Max; Self-Serve moved to a quiet secondary block at bottom; unified CTAs to `/contact/`.
7. Pricing FAQ rewritten — 5 questions matching the brief.
8. **Interactive demo page**: 4 scenarios (Salon/Clinic/Shop/Services) with animated mock chat (typing indicators, status transitions: New → Qualified → Handed). JSON data island + `/static/js/demo.js`.
9. **Shorter contact form**: name + single contact field (Telegram/phone/email) + optional collapsible message + trust badges. CTA renamed to "Получить демо"/"Demo anfordern".
10. **Mobile sticky CTA** (Demo + Telegram), revealed after scroll, auto-removed on `/contact/`.
11. **Solution stubs**: niches without full content (clinic/auto/food/real-estate/retail) now render `solution_stub.html` (not 404) — proper hero + generic 3-step flow + CTAs.
12. **About**: "Как мы работаем"/"So arbeiten wir" 3-step block + revised principles.
13. **SEO**: meta titles/descriptions rewritten for conversion intent on Home/Pricing/Demo (RU+DE).
14. **Lightweight analytics events** (`window.track`): `hero_cta_click`, `secondary_cta_click`, `demo_start`, `demo_scenario_select`, `demo_replay`, `demo_cta_click`, `pricing_plan_click`, `telegram_click`, `lead_form_submit`, `lead_form_success`, `faq_open`, `mobile_sticky_cta_click`, `scroll_50`, `scroll_90`. No-op safe when GA4/Pixel envs are unset.
15. **Footer**: trust copy + Telegram link with track event + "Other-language" link.
16. **Inline lead form** on home (single-step, 2 fields).

**Test coverage:** `/app/backend/tests/test_cro_uplift.py` — pytest suite (39/39 pass) covering hero/trust/cost/flow/industries/stubs/pricing order + self-serve/FAQ/demo/contact/about/SEO/lead endpoint. Playwright verified demo auto-play, scenario switch, mobile sticky behaviour, FAQ toggle.

---

## Architecture map

```
/app/backend/
  server.py                      # FastAPI routes (incl. solution stub fallback)
  config.py                      # ENV
  content/
    ru.py, de.py                 # i18n dicts (full CRO copy)
    blog.py
  templates/
    base.html, home.html, pricing.html, demo.html, contact.html,
    about.html, solutions_index.html, solution_detail.html, solution_stub.html,
    blog_*.html, privacy.html, terms.html, 404.html, language_chooser.html
    partials/
      header.html, footer.html, consent.html
      cta_block.html               # unified CTA pair
      trust_strip.html             # NEW
      mobile_sticky.html           # NEW
      inline_lead_form.html        # NEW
  static/
    css/style.css                  # Tailwind compiled output
    js/
      main.js, forms.js, consent.js
      track.js                     # extended events + mobile-sticky reveal
      demo.js                      # NEW (scenario picker + animated chat)
  tests/
    test_cro_uplift.py             # pytest 39 cases
/app/frontend/
  tailwind.config.js, src/input.css
```

## Env vars (all optional, graceful no-op when missing)
- `MONGO_URL`, `DB_NAME` (required)
- `SITE_URL` — used in canonicals/sitemap
- `TELEGRAM_CTA_URL` — Telegram CTA destination (placeholder in preview env)
- `NEXTBOT_REF_URL` — Self-Serve referral URL
- `GA4_ID` / `META_PIXEL_ID` — analytics (when set, consent-gated load via `consent.js`)

## Key API
- `GET /` (language chooser)
- `GET /{lang}/`, `/{lang}/pricing/`, `/{lang}/demo/`, `/{lang}/solutions/`, `/{lang}/solutions/{slug}/` (full or stub), `/{lang}/about/`, `/{lang}/contact/`, `/{lang}/blog/`, `/{lang}/blog/{slug}/`, `/{lang}/cases/`, `/{lang}/privacy/`, `/{lang}/terms/`
- `POST /api/lead` (5/min rate-limit, honeypot)
- `GET /sitemap.xml`, `/robots.txt`, `/api/health`

---

## Backlog

### P1 — Conversion follow-ups
- Telegram webhook for lead notifications to internal chat.
- Multi-step progressive form on /contact/ (step 2 after submit collects niche+message).
- Lead-magnet PDF (chat-bot launch checklist) gated by email.
- Validation in real time (phone/email format) on contact form.
- A/B test framework when GA4 data starts flowing.

### P2 — Content depth
- Full pages for clinic/auto/food/real-estate/retail (replace stubs with niche-specific problems/how/results).
- Cases section: 3–5 anonymised success scenarios.
- 5 cornerstone blog articles with internal links to pricing.
- Currency display switcher (EUR/USD/UZS) on pricing.
- Pricing comparison table (features × packages).

### P3 — Optimisation
- Lighthouse pass to reach CWV "Good" across the board.
- Replace placeholder `TELEGRAM_CTA_URL` and `NEXTBOT_REF_URL` in production env.
- Schema `Offer.price` numeric normalisation (currently keeps "от $149" string).

---

**Last update:** Feb 2026 — Phase 4 (CRO Uplift Batch) + Phase 5 (Analytics & Telegram lead webhook) completed and tested.

---

## Phase 5 — Analytics & Telegram lead webhook (✅, Feb 2026)

- **GA4** installed (`G-WFZ1VRG0Y7`) — consent-gated load via `consent.js`. `gtag('config', { send_page_view: true, anonymize_ip: true })`.
- **Meta Pixel** installed (`1296661992555792`) — consent-gated load + `<noscript>` fallback in `base.html`. Standard events mapped:
  - `lead_form_success` → **Lead**
  - `telegram_click` → **Contact**
  - `demo_start`, `demo_scenario_select`, `hero_cta_click` → **ViewContent**
  - `demo_cta_click`, `pricing_plan_click` → **InitiateCheckout**
  - All events also fire as `trackCustom` for granular Pixel reports.
- **Event queue** in `track.js`: events fired before consent are buffered (max 50) and flushed via `__onAnalyticsReady` after user accepts cookies — so we don't lose hero/scroll events.
- **Telegram lead webhook** (`server.py` → `notify_telegram_lead`): every successful `/api/lead` insert posts a formatted HTML message to the bot's group chat. Includes name, contact, niche, lead_type, source, message, page URL, referrer, UTMs, timestamp. Best-effort, never blocks the lead flow.

**New env vars:**
- `TELEGRAM_BOT_TOKEN` — bot API token (`@salesdeskbot`)
- `TELEGRAM_LEAD_CHAT_ID` — supergroup ID `-1003903783094` ("Sales Desk Заявки")
- `GA4_ID=G-WFZ1VRG0Y7`
- `META_PIXEL_ID=1296661992555792`
- `TELEGRAM_CTA_URL=https://t.me/salesdeskbot` (was placeholder)
