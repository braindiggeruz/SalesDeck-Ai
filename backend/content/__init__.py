from content.ru import CONTENT_RU
from content.de import CONTENT_DE

CONTENT = {
    "ru": CONTENT_RU,
    "de": CONTENT_DE,
}

def get_content(lang: str) -> dict:
    return CONTENT.get(lang, CONTENT["ru"])
