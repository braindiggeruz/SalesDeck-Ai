import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
NEXTBOT_REF_URL = os.environ.get("NEXTBOT_REF_URL", "")
TELEGRAM_CTA_URL = os.environ.get("TELEGRAM_CTA_URL", "")
GA4_ID = os.environ.get("GA4_ID", "")
META_PIXEL_ID = os.environ.get("META_PIXEL_ID", "")
LEADS_EMAIL = os.environ.get("LEADS_EMAIL", "")

SUPPORTED_LANGS = ["ru", "de"]
DEFAULT_LANG = "ru"
