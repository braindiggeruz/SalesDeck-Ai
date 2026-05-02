"""Backend + SSR tests for SalesDesk AI CRO uplift (iteration 3)."""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"User-Agent": "pytest-cro"})
    return sess


# ---------- Basic availability ----------
def test_health(s):
    r = s.get(f"{BASE_URL}/api/health", timeout=15)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_root_language_chooser(s):
    r = s.get(f"{BASE_URL}/", timeout=15)
    assert r.status_code == 200
    assert "lang" in r.text.lower() or "русск" in r.text.lower() or "deutsch" in r.text.lower()


@pytest.mark.parametrize("lang", ["ru", "de"])
def test_home_200(s, lang):
    r = s.get(f"{BASE_URL}/{lang}/", timeout=15)
    assert r.status_code == 200, r.text[:300]


def test_home_ru_hero_copy(s):
    r = s.get(f"{BASE_URL}/ru/", timeout=15)
    assert r.status_code == 200
    assert "AI-бот отвечает клиентам за секунды" in r.text


def test_home_de_hero_copy(s):
    r = s.get(f"{BASE_URL}/de/", timeout=15)
    assert r.status_code == 200
    assert "Der KI-Bot antwortet Ihren Kunden in Sekunden" in r.text


def test_home_mockup_and_status(s):
    r = s.get(f"{BASE_URL}/ru/", timeout=15)
    assert 'data-testid="hero-mockup"' in r.text
    assert 'data-testid="hero-mockup-status"' in r.text


def test_home_hero_ctas(s):
    r = s.get(f"{BASE_URL}/ru/", timeout=15)
    assert 'data-testid="hero-cta-primary"' in r.text
    assert 'data-testid="hero-cta-secondary"' in r.text
    assert 'href="/ru/demo/"' in r.text
    assert 'href="/ru/contact/"' in r.text
    assert "Получить демо" in r.text
    assert "Обсудить запуск" in r.text
    r2 = s.get(f"{BASE_URL}/de/", timeout=15)
    assert "Demo anfordern" in r2.text
    assert "Implementierung besprechen" in r2.text


def test_home_trust_strip(s):
    r = s.get(f"{BASE_URL}/ru/", timeout=15)
    assert 'data-testid="trust-strip"' in r.text
    for i in range(1, 5):
        assert f'data-testid="trust-item-{i}"' in r.text


def test_home_cost_block(s):
    r = s.get(f"{BASE_URL}/ru/", timeout=15)
    assert 'data-testid="cost-title"' in r.text
    assert "Сколько стоит медленный ответ?" in r.text
    for i in range(1, 4):
        assert f'data-testid="cost-card-{i}"' in r.text
    r2 = s.get(f"{BASE_URL}/de/", timeout=15)
    assert "Was kostet eine langsame Antwort?" in r2.text


def test_home_flow_timeline(s):
    r = s.get(f"{BASE_URL}/ru/", timeout=15)
    for i in range(1, 5):
        assert f'data-testid="flow-step-{i}"' in r.text


def test_home_industries_use_case(s):
    r = s.get(f"{BASE_URL}/ru/", timeout=15)
    # all 7 niches must be present as industry tiles
    for slug in ["beauty", "education", "clinic", "auto", "food", "real-estate", "retail"]:
        assert f'data-testid="industry-{slug}"' in r.text
        assert f'href="/ru/solutions/{slug}/"' in r.text


# ---------- Solutions ----------
@pytest.mark.parametrize("slug", ["clinic", "auto", "food", "real-estate", "retail"])
def test_solution_stub_pages_ru(s, slug):
    r = s.get(f"{BASE_URL}/ru/solutions/{slug}/", timeout=15)
    assert r.status_code == 200, f"{slug}: {r.status_code}"
    assert 'data-testid="solution-stub-title"' in r.text


def test_solution_stub_de_food(s):
    r = s.get(f"{BASE_URL}/de/solutions/food/", timeout=15)
    assert r.status_code == 200
    assert 'data-testid="solution-stub-title"' in r.text


@pytest.mark.parametrize("slug", ["beauty", "education"])
def test_solution_full_detail(s, slug):
    r = s.get(f"{BASE_URL}/ru/solutions/{slug}/", timeout=15)
    assert r.status_code == 200
    assert 'data-testid="solution-hero-title"' in r.text


# ---------- Pricing ----------
@pytest.mark.parametrize("lang", ["ru", "de"])
def test_pricing_packages_order(s, lang):
    r = s.get(f"{BASE_URL}/{lang}/pricing/", timeout=15)
    assert r.status_code == 200
    for tid in ["pricing-card-lite", "pricing-card-pro", "pricing-card-max"]:
        assert f'data-testid="{tid}"' in r.text, f"missing {tid} in {lang}"
    # order
    idx_lite = r.text.find('data-testid="pricing-card-lite"')
    idx_pro = r.text.find('data-testid="pricing-card-pro"')
    idx_max = r.text.find('data-testid="pricing-card-max"')
    assert idx_lite < idx_pro < idx_max


def test_pricing_pro_popular_badge(s):
    r = s.get(f"{BASE_URL}/ru/pricing/", timeout=15)
    assert "Рекомендуем" in r.text
    r2 = s.get(f"{BASE_URL}/de/pricing/", timeout=15)
    assert "Empfohlen" in r2.text


def test_pricing_self_serve_quiet_block(s):
    r = s.get(f"{BASE_URL}/ru/pricing/", timeout=15)
    assert 'data-testid="pricing-self-serve"' in r.text
    assert 'data-testid="pricing-self-serve-cta"' in r.text


def test_pricing_ctas(s):
    r = s.get(f"{BASE_URL}/ru/pricing/", timeout=15)
    # The 3 main cards should CTA to contact (Обсудить запуск)
    assert "Обсудить запуск" in r.text
    assert 'href="/ru/contact/"' in r.text
    r2 = s.get(f"{BASE_URL}/de/pricing/", timeout=15)
    assert "Implementierung besprechen" in r2.text


def test_pricing_faq_five(s):
    r = s.get(f"{BASE_URL}/ru/pricing/", timeout=15)
    for i in range(1, 6):
        assert f'data-testid="pricing-faq-{i}"' in r.text, f"missing pricing-faq-{i}"


# ---------- Demo ----------
def test_demo_scenarios(s):
    r = s.get(f"{BASE_URL}/ru/demo/", timeout=15)
    assert r.status_code == 200
    for k in ["salon", "clinic", "shop", "services"]:
        assert f'data-testid="demo-scenario-{k}"' in r.text, f"missing scenario {k}"
    for tid in ["demo-chat", "demo-messages", "demo-status"]:
        assert f'data-testid="{tid}"' in r.text
    assert 'data-testid="demo-after-contact"' in r.text
    assert "Хочу такой сценарий" in r.text
    r2 = s.get(f"{BASE_URL}/de/demo/", timeout=15)
    assert "Solches Szenario anfragen" in r2.text


# ---------- Contact ----------
def test_contact_form_fields(s):
    r = s.get(f"{BASE_URL}/ru/contact/", timeout=15)
    assert r.status_code == 200
    assert 'data-testid="contact-toggle-message"' in r.text
    assert "Добавить сообщение" in r.text
    assert 'data-testid="contact-trust-badges"' in r.text
    assert 'data-testid="contact-submit-btn"' in r.text
    assert "Получить демо" in r.text


# ---------- API /api/lead ----------
def test_lead_ok(s):
    payload = {"name": "TEST_Auto", "phone": "+7 999 000 0000", "lang": "ru", "source": "pytest"}
    r = s.post(f"{BASE_URL}/api/lead", json=payload, timeout=15)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_lead_missing_name(s):
    r = s.post(f"{BASE_URL}/api/lead", json={"name": "", "phone": "+7 111", "lang": "ru"}, timeout=15)
    assert r.status_code == 400


# ---------- About ----------
@pytest.mark.parametrize("lang,expected", [("ru", "Как мы работаем"), ("de", "So arbeiten wir")])
def test_about_how_block(s, lang, expected):
    r = s.get(f"{BASE_URL}/{lang}/about/", timeout=15)
    assert r.status_code == 200
    assert 'data-testid="about-how-title"' in r.text
    for i in range(1, 4):
        assert f'data-testid="about-how-step-{i}"' in r.text
    assert 'data-testid="about-principles-title"' in r.text
    assert expected in r.text


# ---------- Header / Mobile sticky ----------
def test_header_cta(s):
    r = s.get(f"{BASE_URL}/ru/", timeout=15)
    assert 'data-testid="header-cta"' in r.text
    assert "Получить демо" in r.text


def test_mobile_sticky_on_home(s):
    r = s.get(f"{BASE_URL}/ru/", timeout=15)
    assert 'data-testid="mobile-sticky-cta"' in r.text
    assert 'data-testid="mobile-sticky-demo"' in r.text
    assert 'data-testid="mobile-sticky-telegram"' in r.text


# ---------- Inline lead form ----------
def test_inline_lead_form(s):
    r = s.get(f"{BASE_URL}/ru/", timeout=15)
    assert 'data-testid="inline-lead-form-block"' in r.text
    assert 'data-testid="inline-submit-btn"' in r.text


# ---------- SEO ----------
def test_seo_canonical_hreflang(s):
    for lang in ("ru", "de"):
        r = s.get(f"{BASE_URL}/{lang}/", timeout=15)
        assert 'rel="canonical"' in r.text
        assert 'hreflang="ru"' in r.text
        assert 'hreflang="de"' in r.text


def test_seo_titles(s):
    r = s.get(f"{BASE_URL}/ru/", timeout=15)
    m = re.search(r"<title>(.*?)</title>", r.text, re.S)
    assert m, "no <title>"
    assert "AI-бот для заявок и продаж 24/7" in m.group(1)
    r2 = s.get(f"{BASE_URL}/de/", timeout=15)
    m2 = re.search(r"<title>(.*?)</title>", r2.text, re.S)
    assert m2
    assert "KI-Bot für Anfragen und Vertrieb 24/7" in m2.group(1)


def test_home_schemas_present(s):
    r = s.get(f"{BASE_URL}/ru/", timeout=15)
    assert '"@type": "Organization"' in r.text
    assert '"@type": "WebSite"' in r.text
    assert '"@type": "FAQPage"' in r.text


def test_footer_trust_copy(s):
    r = s.get(f"{BASE_URL}/ru/", timeout=15)
    assert "AI-автоматизация заявок и клиентских диалогов для бизнеса." in r.text
    r2 = s.get(f"{BASE_URL}/de/", timeout=15)
    assert "KI-Automatisierung von Anfragen und Kundendialogen für Unternehmen." in r2.text
