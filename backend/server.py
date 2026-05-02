import os
import json
import logging
import re
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Form, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

from config import (
    MONGO_URL, DB_NAME, SITE_URL, NEXTBOT_REF_URL,
    TELEGRAM_CTA_URL, GA4_ID, META_PIXEL_ID, SUPPORTED_LANGS, DEFAULT_LANG,
    TELEGRAM_BOT_TOKEN, TELEGRAM_LEAD_CHAT_ID, TELEGRAM_WEBHOOK_SECRET
)
from content import get_content
from content.blog import BLOG_POSTS

logger = logging.getLogger("salesdesk")

# --- App ---
app = FastAPI(docs_url=None, redoc_url=None)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"error": "Too many requests"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- DB ---
client = MongoClient(MONGO_URL)
db = client[DB_NAME]
leads_col = db["leads"]

# --- Helpers ---
CURRENT_YEAR = datetime.now().year
OG_IMAGE = "https://static.prod-images.emergentagent.com/jobs/67cc67eb-339d-478f-b80d-965166ef2672/images/be2cd7748fa9fb8296326ab2a0f80021c6732ecb169e268abae3e21bb978d3c8.png"

SOLUTION_SLUGS_WITH_DETAIL = ["beauty", "education"]
ALL_SOLUTION_SLUGS = ["beauty", "education", "clinic", "auto", "food", "real-estate", "retail"]

def validate_lang(lang: str):
    if lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=404)

def base_ctx(request: Request, lang: str, page: str, meta_title: str, meta_desc: str,
             breadcrumbs: list = None, schemas: list = None, og_type: str = "website"):
    c = get_content(lang)
    path_after_lang = str(request.url.path).replace(f"/{lang}/", "").replace(f"/{lang}", "")
    lang_path = path_after_lang if path_after_lang else ""

    canonical = f"{SITE_URL}{request.url.path}"
    if not canonical.endswith("/"):
        canonical += "/"

    other_lang = c["other_lang"]
    other_url = f"{SITE_URL}/{other_lang}/{lang_path}"
    if not other_url.endswith("/"):
        other_url += "/"

    hreflang_links = [
        {"lang": lang, "url": canonical},
        {"lang": other_lang, "url": other_url},
    ]
    x_default = f"{SITE_URL}/"

    if breadcrumbs is None:
        breadcrumbs = []

    if schemas is None:
        schemas = []

    # Always add WebSite + Organization schema on all pages
    org_schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "SalesDesk AI",
        "url": SITE_URL,
        "description": c["footer"]["description"],
    }
    website_schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "SalesDesk AI",
        "url": SITE_URL,
    }
    schemas = [org_schema, website_schema] + schemas

    # Breadcrumb schema
    if breadcrumbs:
        bc_items = []
        for i, bc in enumerate(breadcrumbs):
            bc_items.append({
                "@type": "ListItem",
                "position": i + 1,
                "name": bc["name"],
                "item": bc["url"] if bc.get("url") else None,
            })
        bc_schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": bc_items,
        }
        schemas.append(bc_schema)

    return {
        "request": request,
        "lang": lang,
        "c": c,
        "page": page,
        "meta_title": meta_title,
        "meta_desc": meta_desc,
        "canonical": canonical,
        "hreflang_links": hreflang_links,
        "x_default": x_default,
        "og_type": og_type,
        "schemas": schemas,
        "breadcrumbs": breadcrumbs,
        "telegram_url": TELEGRAM_CTA_URL,
        "ref_url": NEXTBOT_REF_URL,
        "ga4_id": GA4_ID,
        "pixel_id": META_PIXEL_ID,
        "site_url": SITE_URL,
        "current_year": CURRENT_YEAR,
        "lang_path": lang_path,
        "og_image": OG_IMAGE,
    }

def make_breadcrumbs(lang: str, items: list) -> list:
    c = get_content(lang)
    crumbs = [{"name": c["breadcrumbs"]["home"], "url": f"{SITE_URL}/{lang}/"}]
    for key, url in items:
        name = c["breadcrumbs"].get(key, key)
        crumbs.append({"name": name, "url": url})
    return crumbs


# --- Root (Language Chooser) ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    org_schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "SalesDesk AI",
        "url": SITE_URL,
    }
    return templates.TemplateResponse("language_chooser.html", {
        "request": request,
        "site_url": SITE_URL,
        "org_schema": org_schema,
    })


# --- Home ---
@app.get("/{lang}/", response_class=HTMLResponse)
async def home(request: Request, lang: str):
    validate_lang(lang)
    c = get_content(lang)
    p = c["home"]

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}}
            for q in p["faq"]
        ],
    }
    sw_schema = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "SalesDesk AI",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "description": p["meta_desc"],
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    }

    ctx = base_ctx(request, lang, "home", p["meta_title"], p["meta_desc"],
                    schemas=[faq_schema, sw_schema])
    ctx["p"] = p
    return templates.TemplateResponse("home.html", ctx)


# --- Solutions Index ---
@app.get("/{lang}/solutions/", response_class=HTMLResponse)
async def solutions_index(request: Request, lang: str):
    validate_lang(lang)
    c = get_content(lang)
    s = c["solutions"]
    bc = make_breadcrumbs(lang, [("solutions", None)])
    ctx = base_ctx(request, lang, "solutions", s["meta_title"], s["meta_desc"], breadcrumbs=bc)
    return templates.TemplateResponse("solutions_index.html", ctx)


# --- Solution Detail ---
@app.get("/{lang}/solutions/{slug}/", response_class=HTMLResponse)
async def solution_detail(request: Request, lang: str, slug: str):
    validate_lang(lang)
    c = get_content(lang)
    if slug not in c["solutions"]["niches"]:
        raise HTTPException(status_code=404)
    sol = c["solutions"]["niches"][slug]

    bc = make_breadcrumbs(lang, [
        ("solutions", f"{SITE_URL}/{lang}/solutions/"),
        (sol["name"], None),
    ])
    meta_title = sol.get("meta_title") or f"{sol['name']} | SalesDesk AI"
    meta_desc = sol.get("meta_desc") or sol.get("short_desc", "")
    ctx = base_ctx(request, lang, "solutions", meta_title, meta_desc, breadcrumbs=bc)
    ctx["sol"] = sol
    ctx["p"] = c["home"]

    # Full detail page if hero_title + how_it_works exist; otherwise generic stub.
    if sol.get("hero_title") and sol.get("how_it_works"):
        return templates.TemplateResponse("solution_detail.html", ctx)
    return templates.TemplateResponse("solution_stub.html", ctx)


# --- Pricing ---
@app.get("/{lang}/pricing/", response_class=HTMLResponse)
async def pricing(request: Request, lang: str):
    validate_lang(lang)
    c = get_content(lang)
    p = c["pricing"]

    schemas = []
    sw_schema = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "SalesDesk AI",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "offers": [
            {"@type": "Offer", "name": pkg["name"], "description": pkg["subtitle"],
             "price": "0" if "ree" in pkg["price"].lower() or "есплатно" in pkg["price"].lower() else pkg["price"],
             "priceCurrency": "USD" if lang == "ru" else "EUR"}
            for pkg in p["packages"]
        ],
    }
    schemas.append(sw_schema)

    if p.get("faq"):
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}}
                for q in p["faq"]
            ],
        }
        schemas.append(faq_schema)

    bc = make_breadcrumbs(lang, [("pricing", None)])
    ctx = base_ctx(request, lang, "pricing", p["meta_title"], p["meta_desc"], breadcrumbs=bc, schemas=schemas)
    return templates.TemplateResponse("pricing.html", ctx)


# --- Demo ---
@app.get("/{lang}/demo/", response_class=HTMLResponse)
async def demo(request: Request, lang: str):
    validate_lang(lang)
    c = get_content(lang)
    d = c["demo"]

    schemas = []
    if d.get("faq"):
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}}
                for q in d["faq"]
            ],
        }
        schemas.append(faq_schema)

    bc = make_breadcrumbs(lang, [("demo", None)])
    ctx = base_ctx(request, lang, "demo", d["meta_title"], d["meta_desc"], breadcrumbs=bc, schemas=schemas)
    return templates.TemplateResponse("demo.html", ctx)


# --- Blog Index ---
@app.get("/{lang}/blog/", response_class=HTMLResponse)
async def blog_index(request: Request, lang: str):
    validate_lang(lang)
    c = get_content(lang)
    b = c["blog"]
    posts = BLOG_POSTS.get(lang, [])
    bc = make_breadcrumbs(lang, [("blog", None)])
    ctx = base_ctx(request, lang, "blog", b["meta_title"], b["meta_desc"], breadcrumbs=bc)
    ctx["posts"] = posts
    return templates.TemplateResponse("blog_index.html", ctx)


# --- Blog Post ---
@app.get("/{lang}/blog/{slug}/", response_class=HTMLResponse)
async def blog_post(request: Request, lang: str, slug: str):
    validate_lang(lang)
    c = get_content(lang)
    posts = BLOG_POSTS.get(lang, [])
    post = next((p for p in posts if p["slug"] == slug), None)
    if not post:
        raise HTTPException(status_code=404)

    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post["title"],
        "description": post["excerpt"],
        "datePublished": post["date"],
        "author": {"@type": "Organization", "name": "SalesDesk AI"},
        "publisher": {"@type": "Organization", "name": "SalesDesk AI"},
    }

    bc = make_breadcrumbs(lang, [
        ("blog", f"{SITE_URL}/{lang}/blog/"),
        (post["title"][:40], None),
    ])
    ctx = base_ctx(request, lang, "blog", f"{post['title']} | SalesDesk AI",
                    post["excerpt"], breadcrumbs=bc, schemas=[article_schema], og_type="article")
    ctx["post"] = post
    return templates.TemplateResponse("blog_post.html", ctx)


# --- About ---
@app.get("/{lang}/about/", response_class=HTMLResponse)
async def about(request: Request, lang: str):
    validate_lang(lang)
    c = get_content(lang)
    a = c["about"]
    bc = make_breadcrumbs(lang, [("about", None)])
    ctx = base_ctx(request, lang, "about", a["meta_title"], a["meta_desc"], breadcrumbs=bc)
    return templates.TemplateResponse("about.html", ctx)


# --- Contact ---
@app.get("/{lang}/contact/", response_class=HTMLResponse)
async def contact(request: Request, lang: str):
    validate_lang(lang)
    c = get_content(lang)
    ct = c["contact"]
    bc = make_breadcrumbs(lang, [("contact", None)])
    ctx = base_ctx(request, lang, "contact", ct["meta_title"], ct["meta_desc"], breadcrumbs=bc)
    return templates.TemplateResponse("contact.html", ctx)


# --- Privacy ---
@app.get("/{lang}/privacy/", response_class=HTMLResponse)
async def privacy(request: Request, lang: str):
    validate_lang(lang)
    c = get_content(lang)
    p = c["privacy"]
    bc = make_breadcrumbs(lang, [("privacy", None)])
    ctx = base_ctx(request, lang, "privacy", p["meta_title"], p["meta_desc"], breadcrumbs=bc)
    return templates.TemplateResponse("privacy.html", ctx)


# --- Terms ---
@app.get("/{lang}/terms/", response_class=HTMLResponse)
async def terms(request: Request, lang: str):
    validate_lang(lang)
    c = get_content(lang)
    t = c["terms"]
    bc = make_breadcrumbs(lang, [("terms", None)])
    ctx = base_ctx(request, lang, "terms", t["meta_title"], t["meta_desc"], breadcrumbs=bc)
    return templates.TemplateResponse("terms.html", ctx)


# --- Cases ---
@app.get("/{lang}/cases/", response_class=HTMLResponse)
async def cases(request: Request, lang: str):
    validate_lang(lang)
    c = get_content(lang)
    cs = c["cases"]
    bc = make_breadcrumbs(lang, [("cases", None)])
    ctx = base_ctx(request, lang, "cases", cs["meta_title"], cs["meta_desc"], breadcrumbs=bc)
    return templates.TemplateResponse("cases.html", ctx)


# --- API: Lead Form ---
@app.post("/api/lead")
@limiter.limit("5/minute")
async def submit_lead(request: Request):
    try:
        data = await request.json()
    except Exception:
        form = await request.form()
        data = dict(form)

    # Honeypot check (silent ok)
    if data.get("website"):
        return JSONResponse({"status": "ok"})

    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    business = str(data.get("business", "")).strip()
    message = str(data.get("message", "")).strip()
    lang = str(data.get("lang", "ru")).strip()
    source = str(data.get("source", "unknown")).strip()
    lead_type = str(data.get("lead_type", "implementation")).strip()
    page_url = str(data.get("page_url", "")).strip()
    referrer = str(data.get("referrer", "")).strip()

    if not name or not phone:
        return JSONResponse(status_code=400, content={"error": "name and phone required"})
    if len(name) > 200 or len(phone) > 100 or len(message) > 2000:
        return JSONResponse(status_code=400, content={"error": "input too long"})

    lead_id = uuid.uuid4().hex[:12]  # short id, used in callback_data + Pixel eventID
    lead = {
        "lead_id": lead_id,
        "name": name,
        "phone": phone,
        "business": business,
        "message": message,
        "lang": lang,
        "source": source,
        "lead_type": lead_type,
        "page_url": page_url,
        "referrer": referrer,
        "utm_source": str(data.get("utm_source", "")).strip(),
        "utm_medium": str(data.get("utm_medium", "")).strip(),
        "utm_campaign": str(data.get("utm_campaign", "")).strip(),
        "utm_content": str(data.get("utm_content", "")).strip(),
        "utm_term": str(data.get("utm_term", "")).strip(),
        "status": "new",
        "telegram_sent": False,
        "telegram_message_id": None,
        "telegram_error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    leads_col.insert_one(lead)

    # Best-effort Telegram notification — never breaks lead flow.
    try:
        await notify_telegram_lead(lead)
    except Exception as e:
        logger.warning("Telegram notify outer error: %s", type(e).__name__)

    # Return lead_id so the frontend can use it as Pixel eventID for dedup with future CAPI.
    return JSONResponse({"status": "ok", "lead_id": lead_id, "message": "Lead received"})


# --- Telegram: helpers ---

# In-memory dedup of callback_query_id (~5 min TTL) to avoid replay spam.
_callback_dedup: dict = {}

def _safe_text(s) -> str:
    if not s:
        return ""
    s = str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _build_contact_url(phone: str) -> Optional[str]:
    """Return a tel:/mailto:/t.me URL only when contact is unambiguously parseable."""
    if not phone:
        return None
    p = phone.strip()
    if p.startswith("@") and re.match(r"^@[A-Za-z0-9_]{4,32}$", p):
        return f"https://t.me/{p[1:]}"
    if "@" in p and re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", p):
        return f"mailto:{p}"
    digits = re.sub(r"[^\d+]", "", p)
    if re.match(r"^\+?\d{7,15}$", digits):
        return f"tel:{digits}"
    return None

STATUS_LABEL = {
    "new":       "🟢 Новая",
    "processed": "✅ Обработана",
    "archived":  "🗄 В архиве",
}

def _build_keyboard(lead_id: str, status: str, contact_url: Optional[str]):
    rows = []
    if contact_url:
        rows.append([{"text": "💬 Связаться", "url": contact_url}])
    if status == "new":
        rows.append([
            {"text": "✅ Обработано", "callback_data": f"done:{lead_id}"},
            {"text": "🗄 Архив",       "callback_data": f"arch:{lead_id}"},
        ])
    elif status == "processed":
        rows.append([
            {"text": "↩️ Вернуть в работу", "callback_data": f"back:{lead_id}"},
            {"text": "🗄 Архив",            "callback_data": f"arch:{lead_id}"},
        ])
    elif status == "archived":
        rows.append([
            {"text": "↩️ Вернуть в работу", "callback_data": f"back:{lead_id}"},
        ])
    return {"inline_keyboard": rows}

def _format_lead_text(lead: dict, status: str = "new") -> str:
    lang = lead.get("lang", "")
    flag = "🇷🇺" if lang == "ru" else ("🇩🇪" if lang == "de" else "🌐")
    utm_bits = []
    for k in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"):
        v = lead.get(k)
        if v:
            utm_bits.append(f"<i>{_safe_text(k)}</i>: {_safe_text(v)}")
    utm_block = ("\n" + " · ".join(utm_bits)) if utm_bits else ""
    referrer = lead.get("referrer") or "—"

    return (
        f"{flag} <b>Новая заявка · SalesDesk AI</b>\n"
        f"<i>Статус: {STATUS_LABEL.get(status, status)}</i>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 <b>Имя:</b> {_safe_text(lead.get('name'))}\n"
        f"📞 <b>Контакт:</b> <code>{_safe_text(lead.get('phone'))}</code>\n"
        f"🏷 <b>Ниша:</b> {_safe_text(lead.get('business') or '—')}\n"
        f"🎯 <b>Тип:</b> {_safe_text(lead.get('lead_type'))}\n"
        f"📍 <b>Источник:</b> {_safe_text(lead.get('source'))}\n"
        f"💬 <b>Сообщение:</b> {_safe_text(lead.get('message') or '—')}\n"
        f"🔗 <b>Страница:</b> {_safe_text(lead.get('page_url'))}\n"
        f"↩️ <b>Referrer:</b> {_safe_text(referrer)}"
        f"{utm_block}\n"
        f"🕐 {_safe_text(lead.get('created_at'))}\n"
        f"<code>id: {_safe_text(lead.get('lead_id'))}</code>"
    )

async def _telegram_post(method: str, payload: dict, retries: int = 2) -> Optional[dict]:
    """POST to Telegram Bot API with timeout + small retry. Returns response JSON or None on failure."""
    if not TELEGRAM_BOT_TOKEN:
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    last_err = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.post(url, json=payload)
            if r.status_code == 200:
                data = r.json()
                if data.get("ok"):
                    return data
                last_err = f"telegram_not_ok:{data.get('error_code')}"
                # Don't retry on 4xx client errors (chat_not_found, blocked etc.)
                if data.get("error_code") and 400 <= data["error_code"] < 500:
                    break
            else:
                last_err = f"http_{r.status_code}"
                if 400 <= r.status_code < 500:
                    break
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last_err = f"net_{type(e).__name__}"
        except Exception as e:
            last_err = f"err_{type(e).__name__}"
        if attempt < retries:
            await asyncio.sleep(0.5 * (attempt + 1))
    logger.warning("Telegram %s failed: %s", method, last_err)
    return None

async def notify_telegram_lead(lead: dict):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_LEAD_CHAT_ID:
        return
    text = _format_lead_text(lead, "new")
    keyboard = _build_keyboard(lead["lead_id"], "new", _build_contact_url(lead.get("phone")))
    payload = {
        "chat_id": TELEGRAM_LEAD_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": keyboard,
    }
    resp = await _telegram_post("sendMessage", payload)
    if resp and resp.get("ok"):
        msg_id = resp.get("result", {}).get("message_id")
        leads_col.update_one(
            {"lead_id": lead["lead_id"]},
            {"$set": {
                "telegram_sent": True,
                "telegram_message_id": msg_id,
                "telegram_chat_id": TELEGRAM_LEAD_CHAT_ID,
            }}
        )
    else:
        leads_col.update_one(
            {"lead_id": lead["lead_id"]},
            {"$set": {"telegram_sent": False, "telegram_error": "send_failed"}}
        )


# --- Telegram: callback webhook (manager buttons) ---
@app.post("/api/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(default=None),
):
    # Require secret token. If TELEGRAM_WEBHOOK_SECRET not configured, refuse all.
    if not TELEGRAM_WEBHOOK_SECRET or x_telegram_bot_api_secret_token != TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="forbidden")

    try:
        update = await request.json()
    except Exception:
        return JSONResponse({"ok": True})

    cb = update.get("callback_query")
    if not cb:
        return JSONResponse({"ok": True})

    cb_id = cb.get("id")
    if not cb_id:
        return JSONResponse({"ok": True})

    # Replay protection (in-memory, ~5 min TTL)
    now = datetime.now(timezone.utc).timestamp()
    expired = [k for k, ts in _callback_dedup.items() if now - ts > 300]
    for k in expired:
        _callback_dedup.pop(k, None)
    if cb_id in _callback_dedup:
        return JSONResponse({"ok": True})
    _callback_dedup[cb_id] = now

    raw = (cb.get("data") or "").strip()
    if ":" not in raw:
        await _telegram_post("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Invalid"})
        return JSONResponse({"ok": True})

    action, lead_id = raw.split(":", 1)
    if not re.match(r"^[a-f0-9]{6,32}$", lead_id) or action not in ("done", "arch", "back"):
        await _telegram_post("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Invalid"})
        return JSONResponse({"ok": True})

    new_status = {"done": "processed", "arch": "archived", "back": "new"}[action]
    actor = (cb.get("from") or {}).get("username") or str((cb.get("from") or {}).get("id") or "")

    lead = leads_col.find_one({"lead_id": lead_id}, {"_id": 0})
    if not lead:
        await _telegram_post("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Lead not found", "show_alert": True})
        return JSONResponse({"ok": True})

    leads_col.update_one(
        {"lead_id": lead_id},
        {"$set": {"status": new_status, "status_updated_at": datetime.now(timezone.utc).isoformat(), "status_actor": actor}}
    )
    lead["status"] = new_status

    msg = cb.get("message") or {}
    chat_id = (msg.get("chat") or {}).get("id")
    msg_id = msg.get("message_id")

    # Edit message text + keyboard to reflect new status
    if chat_id and msg_id:
        await _telegram_post("editMessageText", {
            "chat_id": chat_id,
            "message_id": msg_id,
            "text": _format_lead_text(lead, new_status),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": _build_keyboard(lead_id, new_status, _build_contact_url(lead.get("phone"))),
        })

    await _telegram_post("answerCallbackQuery", {
        "callback_query_id": cb_id,
        "text": f"Статус: {STATUS_LABEL.get(new_status, new_status)}",
    })
    return JSONResponse({"ok": True})


# --- Sitemap ---
@app.get("/sitemap.xml", response_class=Response)
async def sitemap():
    pages = []
    for lang in SUPPORTED_LANGS:
        pages.append(f"/{lang}/")
        for p in ["solutions", "pricing", "demo", "blog", "about", "contact", "privacy", "terms", "cases"]:
            pages.append(f"/{lang}/{p}/")
        for slug in ALL_SOLUTION_SLUGS:
            pages.append(f"/{lang}/solutions/{slug}/")
        for post in BLOG_POSTS.get(lang, []):
            pages.append(f"/{lang}/blog/{post['slug']}/")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
    xml += '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'

    # Root
    xml += '  <url>\n'
    xml += f'    <loc>{SITE_URL}/</loc>\n'
    xml += '    <changefreq>monthly</changefreq>\n'
    xml += '    <priority>0.5</priority>\n'
    xml += '  </url>\n'

    for page_path in pages:
        url = f"{SITE_URL}{page_path}"
        lang = page_path.split("/")[1]
        other_lang = "de" if lang == "ru" else "ru"
        other_path = page_path.replace(f"/{lang}/", f"/{other_lang}/")
        other_url = f"{SITE_URL}{other_path}"

        priority = "1.0" if page_path.endswith(f"/{lang}/") else "0.8"
        if "/blog/" in page_path and page_path.count("/") > 3:
            priority = "0.6"

        xml += '  <url>\n'
        xml += f'    <loc>{url}</loc>\n'
        xml += f'    <xhtml:link rel="alternate" hreflang="{lang}" href="{url}"/>\n'
        xml += f'    <xhtml:link rel="alternate" hreflang="{other_lang}" href="{other_url}"/>\n'
        xml += f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE_URL}/"/>\n'
        xml += f'    <changefreq>weekly</changefreq>\n'
        xml += f'    <priority>{priority}</priority>\n'
        xml += '  </url>\n'

    xml += '</urlset>'
    return Response(content=xml, media_type="application/xml")


# --- Robots.txt ---
@app.get("/robots.txt", response_class=Response)
async def robots():
    content = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")


# --- Health ---
@app.get("/api/health")
async def health():
    return {"status": "ok"}


# --- 404 Handler ---
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    path = str(request.url.path)
    lang = DEFAULT_LANG
    for l in SUPPORTED_LANGS:
        if path.startswith(f"/{l}/") or path == f"/{l}":
            lang = l
            break

    c = get_content(lang)
    ctx = base_ctx(request, lang, "404", c["not_found"]["title"], c["not_found"]["desc"])
    return templates.TemplateResponse("404.html", ctx, status_code=404)
