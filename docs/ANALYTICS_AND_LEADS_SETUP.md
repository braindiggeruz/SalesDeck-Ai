# Analytics & Lead Notifications — Manual Setup

Production-hardening checklist for SalesDesk AI.

---

## 1. Google Analytics 4

**Property:** `G-WFZ1VRG0Y7`

### Mark conversions (Key Events)
1. Open **GA4 → Admin → Data display → Events** (or **Conversions** in some UIs).
2. Locate `lead_form_success` after the first event arrives (Realtime tab confirms delivery).
3. Toggle **Mark as key event** (replaces the old "Conversion" terminology).
4. Optionally also mark `demo_cta_click` and `pricing_plan_click` as key events for funnel attribution.

### Recommended custom dimensions (Admin → Custom definitions)
Register these so GA4 retains them in reports:

| Parameter        | Type   | Used by                                        |
|------------------|--------|------------------------------------------------|
| `cta_location`   | Event  | `hero_cta_click`, `secondary_cta_click`, all CTAs |
| `plan_name`      | Event  | `pricing_plan_click`                           |
| `scenario_name`  | Event  | `demo_scenario_select`                         |
| `lead_type`      | Event  | `lead_form_success`                            |
| `business_type`  | Event  | `lead_form_success`                            |
| `language`       | Event  | All events (auto-injected)                     |

`page_path` and `page_location` are GA4 built-ins — no setup needed.

---

## 2. Meta Pixel

**Pixel ID:** `1296661992555792`

### Standard events automatically fired
| Internal event        | Pixel standard event |
|-----------------------|----------------------|
| `lead_form_success`   | **Lead** (eventID = `lead_id` for future CAPI dedup) |
| `telegram_click`      | **Contact**          |
| `demo_start`, `demo_scenario_select`, `hero_cta_click` | **ViewContent** |
| `demo_cta_click`, `pricing_plan_click` | **InitiateCheckout** |

Every internal event additionally fires as `trackCustom` with the original name for granular segmentation.

### Custom Conversion (recommended)
1. **Events Manager → Custom Conversions → Create**.
2. Source = the SalesDesk AI Pixel.
3. Trigger = **Standard event "Lead"**.
4. Optional rule: `lead_type` ∈ {`demo`, `implementation`}.
5. Use this Custom Conversion as the optimisation goal in Ads Manager.

### Verify with Pixel Helper
- Install the **Meta Pixel Helper** Chrome extension.
- Open the site → accept cookies → submit the contact form.
- Helper should show: `PageView`, `Lead` (with `eventID`), and `lead_form_success` (custom).

### Conversions API (optional, future)
Backend already issues `lead_id` per submission and the frontend passes it as Pixel `eventID`. To deduplicate when CAPI is added, the server should send the same `event_id` in the Conversions API call.

---

## 3. Telegram Lead Notifications

**Bot:** `@salesdeskbot`
**Group:** "Sales Desk Заявки" (chat_id `-1003903783094`, supergroup format).

### Verify the channel
```
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getChat?chat_id=${TELEGRAM_LEAD_CHAT_ID}"
```
Expect `"ok": true` and `"type": "supergroup"`.

### Send a manual test
```
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_LEAD_CHAT_ID}" \
  -d "text=manual ping"
```

### Send a test lead via the API
```
curl -s -X POST "${SITE_URL}/api/lead" \
  -H "Content-Type: application/json" \
  -d '{"name":"TEST","phone":"@test_user","lang":"ru","source":"manual_test","lead_type":"demo"}'
```
Expect `{"status":"ok","lead_id":"…"}`. The group should receive an HTML card with inline buttons.

---

## 4. Telegram Manager Buttons (callback webhook)

The lead message includes inline buttons:
- 💬 **Связаться** (only when contact is unambiguously a Telegram username, email, or phone).
- ✅ **Обработано** / 🗄 **Архив** / ↩️ **Вернуть в работу**

Status is persisted in Mongo (`leads.status` = `new` | `processed` | `archived`).
The card is edited in-place to reflect the current status.

### Register the callback webhook
The endpoint is `POST /api/telegram/webhook` and is **secret-token gated**.

1. Generate a secure secret (≥ 32 chars, ASCII only) and put it in `backend/.env` as `TELEGRAM_WEBHOOK_SECRET`. Restart backend.
2. Tell Telegram to deliver updates to it:
   ```
   curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
     -d "url=${SITE_URL}/api/telegram/webhook" \
     -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}" \
     -d "allowed_updates=[\"callback_query\"]"
   ```
3. Verify:
   ```
   curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
   ```
   `pending_update_count` should drop to 0 and `last_error_date` should be empty.

### Webhook safety
- Without `TELEGRAM_WEBHOOK_SECRET` set, the endpoint returns **403** for every request.
- Telegram sends the secret in the header `X-Telegram-Bot-Api-Secret-Token`; mismatched secret → 403.
- `callback_query` IDs are deduplicated in-memory for ~5 minutes against replay.
- Lead status changes are logged with the Telegram username/ID of the actor (`status_actor`).

### Remove the webhook (rollback)
```
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook"
```

---

## 5. Environment variables (names only)

| Var                       | Purpose                                     |
|---------------------------|---------------------------------------------|
| `MONGO_URL`               | Mongo connection string (required)          |
| `DB_NAME`                 | Mongo database name (required)              |
| `SITE_URL`                | Public origin used in canonicals/sitemap    |
| `GA4_ID`                  | Google Analytics 4 measurement ID           |
| `META_PIXEL_ID`           | Meta Pixel ID                               |
| `TELEGRAM_BOT_TOKEN`      | Bot API token                               |
| `TELEGRAM_LEAD_CHAT_ID`   | Group/chat ID for lead notifications        |
| `TELEGRAM_WEBHOOK_SECRET` | Secret token used to authorise the callback webhook |
| `TELEGRAM_CTA_URL`        | Public Telegram URL for the CTA buttons     |
| `NEXTBOT_REF_URL`         | Self-Serve referral URL                     |

> The site is a server-rendered FastAPI app — there are **no `NEXT_PUBLIC_*`** variables. Front-end JS reads the GA4/Pixel IDs from `<html data-ga4>` / `<html data-pixel>` attributes which are set server-side from the env. No tokens or secrets are exposed to the browser.

---

## 6. Hardening notes

- **Lead flow never breaks on Telegram failure.** The notifier has a 5 s timeout and up to 2 retries; on permanent failure the lead is still saved and the API returns `{"status":"ok"}` with the `lead_id`.
- **Single-fire `Lead`.** `forms.js` permanently disables the submit button after success and `track.js` deduplicates `lead_form_success` per page load.
- **Consent gating.** Nothing leaves the browser before the user accepts cookies; events fired pre-consent are queued (max 50) and flushed once GA4/Pixel load.
- **No PII in Pixel payloads.** Only whitelisted, non-PII fields are forwarded to FB (`plan_name`, `scenario_name`, `cta_location`, `lead_type`, `business_type`, `language`); name/phone/message never leave the backend.
