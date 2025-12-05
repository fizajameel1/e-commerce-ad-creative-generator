"""
inference/generator.py

Load the template baseline and produce ad creative(s).

Functions:
- load_model(path) -> model dict
- generate_creative(title, description, category, model, variant_idx=None) -> str

This is intentionally lightweight and deterministic.
"""

from pathlib import Path
import json
import textwrap


def load_model(path: str | Path) -> dict:
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _shorten_description(description: str, max_words: int) -> str:
    words = description.strip().split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(" ") + "..."


def generate_creative(title: str, description: str, category: str, model: dict, variant_idx: int | None = None) -> str:
    title = (title or "").strip()
    description = (description or "").strip()
    category = (category or "general").strip().lower()

    # pick short description
    short_desc = _shorten_description(description, model.get("short_desc_max_words", 20))

    # choose CTAs for category or fallback
    ctas = model.get("category_ctas", {}).get(category, None)
    if not ctas:
        # fallback pick deterministic CTA
        ctas = model.get("category_ctas", {}).get("general", []) or ["Shop now"]

    # choose template variant
    variants = model.get("template_variants", ["{title} — {short_desc} {cta}."])
    if variant_idx is None:
        # deterministic selection based on title hash for variety
        variant_idx = abs(hash(title + category)) % len(variants)
    template = variants[variant_idx]

    # deterministic CTA selection
    cta = ctas[abs(hash(title + description)) % len(ctas)]

    creative = template.format(title=title, short_desc=short_desc, cta=cta)
    # tidy whitespace and ensure punctuation
    creative = " ".join(creative.split())
    # capitalize first letter if missing
    if creative and not creative[0].isupper():
        creative = creative[0].upper() + creative[1:]
    return creative
