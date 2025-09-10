# stages/backcover.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from core.models import ModelBundle, Block
from core.render import render_fragment

def _first_backcover_block(model: ModelBundle) -> Optional[Block]:
    for b in model.blocks:
        if str(b.type).lower() == "backcover":
            return b
    return None

def _get_param(b: Optional[Block], settings, key: str, default: Any = None) -> Any:
    if b and isinstance(b.params, dict) and key in b.params and b.params[key] not in (None, ""):
        return b.params[key]
    v = settings.get(key, "")
    if v != "":
        return v
    return default

def _norm_url(p: Optional[str]) -> Optional[str]:
    return None if p is None else str(p).replace("\\", "/").strip()

def _assets_root(settings):
    base = settings.get("assets_base", "")
    if isinstance(base, str) and base.startswith("file://"):
        return Path(urlparse(base).path)
    return None

def _exists(rel_url: Optional[str], settings) -> bool:
    root = _assets_root(settings)
    if not (root and rel_url):
        return False
    return (root / rel_url).resolve().exists()

def generate_backcover(template_dir: Path, model: ModelBundle) -> str:
    settings = model.settings
    b = _first_backcover_block(model)

    # Источники: без лого и QR
    bg_img   = _norm_url(_get_param(b, settings, "backcover_bg", None) or _get_param(b, settings, "bg", None))
    bg_color = _get_param(b, settings, "backcover_bg_color", None) or settings.get("theme_color", "#d32f2f")
    logo_img_src = _norm_url(_get_param(b, settings, "backcover_logo", None))


    text     = _get_param(b, settings, "backcover_text", "") or ""
    c_name   = _get_param(b, settings, "company_name", "")
    c_addr   = _get_param(b, settings, "company_address", "")
    c_cont   = _get_param(b, settings, "company_contacts", settings.get("contacts",""))
    c_site   = _get_param(b, settings, "company_site", "")
    
    text_size_pt = int(_get_param(b, settings, "backcover_text_size_pt", 12))
    gap_mm       = float(_get_param(b, settings, "backcover_gap_mm", 8))

    ctx: Dict[str, Any] = {
        "bg_img": bg_img,
        "bg_img_exists": _exists(bg_img, settings),
        "bg_color": bg_color,

        "text": text,
        "text_size_pt": text_size_pt,

        "company_name": c_name,
        "company_address": c_addr,
        "company_contacts": c_cont,
        "company_site": c_site,
        "logo": logo_img_src,

        "gap_mm": gap_mm,
        "page_break_before": True,
    }

    return render_fragment(template_dir, "backcover.html.j2", ctx)
