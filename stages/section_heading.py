# stages/section_heading.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List

from core.models import ModelBundle, Block
from core.render import render_fragment


def render_all_section_headings(template_dir: Path, model: ModelBundle) -> List[str]:
    """
    Проходит по блокам section_heading и рендерит их через templates/section_heading.html.j2.
    Полезно, если заголовки выводятся как самостоятельные страницы/полосы.
    """
    out: List[str] = []
    logo = model.settings.get("cover_logo", "")  # можно задать другой ключ
    for b in model.blocks:
        if str(b.type).lower() != "section_heading":
            continue

        # series_code можно прокинуть через b.params.series_code; иначе оставим пустым
        ctx_b: Dict[str, Any] = {
            "block_id": b.block_id,
            "title": b.title or "",
            "subtitle": b.subtitle or "",
            "series_code": (b.params or {}).get("series_code") or "",
            "logo": logo,
        }
        out.append(render_fragment(template_dir, "section_heading.html.j2", {"b": ctx_b}))
    return out
