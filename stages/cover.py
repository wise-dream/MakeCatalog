from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from core.models import ModelBundle, Block
from core.render import render_fragment

def _first_cover_block(model: ModelBundle) -> Optional[Block]:
    for b in model.blocks:
        if b.type in ("cover", "hero"):
            return b
    return None

def _get_param(b: Optional[Block], settings, key: str, default: Any = None) -> Any:
    if b and isinstance(b.params, dict) and key in b.params and b.params[key] not in (None, ""):
        return b.params[key]
    val = settings.get(key, "")
    if val != "":
        return val
    return default

def _norm_url(p: Optional[str]) -> Optional[str]:
    if p is None:
        return None
    return str(p).replace("\\", "/").strip()

def _assets_root(settings) -> Optional[Path]:
    base = settings.get("assets_base", "")
    if isinstance(base, str) and base.startswith("file://"):
        return Path(urlparse(base).path)
    return None

def _abs_from_assets(rel_url: Optional[str], settings) -> Optional[Path]:
    root = _assets_root(settings)
    if not (root and rel_url):
        return None
    return (root / rel_url).resolve()

def _read_svg(abs_path: Optional[Path]) -> Optional[str]:
    if not abs_path:
        return None
    try:
        return abs_path.read_text(encoding="utf-8")
    except Exception:
        return None

def generate_cover(template_dir: Path, model: ModelBundle) -> str:
    settings = model.settings
    b = _first_cover_block(model)

    # данные
    bg_rel   = _norm_url(_get_param(b, settings, "bg", None)   or _get_param(None, settings, "cover_bg", None))
    logo_rel = _norm_url(_get_param(b, settings, "logo", None) or _get_param(None, settings, "cover_logo", None))
    year     = _get_param(b, settings, "year", "")
    subtitle = _get_param(b, settings, "subtitle", "")

    # визуал
    overlay_opacity = float(_get_param(b, settings, "overlay_opacity", 0.4))
    v_align         = _get_param(b, settings, "v_align", "center")  # top|center|bottom
    logo_max_w_mm   = float(_get_param(b, settings, "logo_max_w_mm", 80))
    logo_max_h_mm   = float(_get_param(b, settings, "logo_max_h_mm", 40))
    gap_mm          = float(_get_param(b, settings, "gap_mm", 6))
    title_size_pt   = int(_get_param(b, settings, "title_size_pt", 36))
    subtitle_size_pt= int(_get_param(b, settings, "subtitle_size_pt", 16))
    title_color     = _get_param(b, settings, "title_color", "#FFFFFF")
    subtitle_color  = _get_param(b, settings, "subtitle_color", "rgba(255,255,255,.95)")
    title_shadow    = _get_param(b, settings, "title_shadow", "0 2px 10px rgba(0,0,0,.35)")
    brand_color     = settings.get("theme_color", "#E53935")

    if v_align not in ("top", "center", "bottom"):
        v_align = "center"
    place_items = {"top": "start", "center": "center", "bottom": "end"}[v_align]

    # фон
    bg_abs = _abs_from_assets(bg_rel, settings)
    bg_exists = bool(bg_abs and bg_abs.exists())

    # логотип: SVG inline при возможности, иначе <img>, плюс флаг существования файла
    logo_svg_inline: Optional[str] = None
    logo_img_src: Optional[str] = None
    logo_abs = _abs_from_assets(logo_rel, settings)
    logo_exists = bool(logo_abs and logo_abs.exists())

    if logo_rel:
        if logo_rel.lower().endswith(".svg"):
            svg_text = _read_svg(logo_abs) if logo_exists else None
            if svg_text:
                logo_svg_inline = svg_text
            else:
                # fallback: пусть будет <img src="…svg">, браузер покажет, а в PDF возьмём chromium при надобности
                logo_img_src = logo_rel
        else:
            logo_img_src = logo_rel

    ctx: Dict[str, Any] = {
        "bg": bg_rel,
        "bg_exists": bg_exists,
        "bg_abs": str(bg_abs) if bg_abs else "",
        "logo": logo_img_src,
        "logo_exists": logo_exists,
        "logo_abs": str(logo_abs) if logo_abs else "",
        "logo_svg_inline": logo_svg_inline,
        "year": year,
        "subtitle": subtitle,
        "overlay_opacity": overlay_opacity,
        "place_items": place_items,
        "logo_max_w_mm": logo_max_w_mm,
        "logo_max_h_mm": logo_max_h_mm,
        "gap_mm": gap_mm,
        "title_size_pt": title_size_pt,
        "subtitle_size_pt": subtitle_size_pt,
        "title_color": title_color,
        "subtitle_color": subtitle_color,
        "title_shadow": title_shadow,
        "brand_color": brand_color,
        "page_break_before": True,
    }
    return render_fragment(template_dir, "cover.html.j2", ctx)
