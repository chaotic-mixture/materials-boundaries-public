"""Presentation-only localization. Stable scientific identifiers never change."""
from collections.abc import Callable

from .catalog import read_catalog

LANGUAGES = ("zh", "en", "ja", "de")


def translate(key: str, language: str = "en") -> str:
    if language not in LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    languages = read_catalog("locales")["languages"]
    return languages.get(language, {}).get(key, languages.get("en", {}).get(key, f"[missing:{key}]"))


def _catalog_translation_lookup(language: str) -> Callable[[str], str]:
    """Make one lazy locale snapshot for one catalog render, never shared.

    Defer the language check and read until the first label to preserve render
    error ordering. Keep the standalone translation API's fresh-read behavior.
    """
    languages = None

    def lookup(key: str) -> str:
        nonlocal languages
        if language not in LANGUAGES:
            raise ValueError(f"unsupported language: {language}")
        if languages is None:
            languages = read_catalog("locales")["languages"]
        return languages.get(language, {}).get(key, languages.get("en", {}).get(key, f"[missing:{key}]"))

    return lookup
