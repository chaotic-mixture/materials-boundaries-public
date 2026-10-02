"""Presentation-only localization. Stable scientific identifiers never change."""
from .catalog import read_catalog

LANGUAGES = ("zh", "en", "ja", "de")


def translate(key: str, language: str = "en") -> str:
    if language not in LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    languages = read_catalog("locales")["languages"]
    return languages.get(language, {}).get(key, languages.get("en", {}).get(key, f"[missing:{key}]"))
