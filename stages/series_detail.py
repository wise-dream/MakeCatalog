# stages/series_detail.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import re
import uuid

from core.models import ModelBundle, Block, Section, Series
from core.render import render_fragment


def _is_series_heading(b: Block) -> bool:
    if str(getattr(b, "type", "")).lower() != "section_heading":
        return False
    lvl = None
    params = b.params or {}
    try:
        lvl = int(params.get("toc_level"))
    except Exception:
        pass
    return lvl == 2


def _series_block_id(model: ModelBundle, series_name: str) -> Optional[str]:
    """Находим block_id заголовка серии (L2), чтобы привязать якоря страниц серии."""
    for b in model.blocks:
        if _is_series_heading(b) and (b.title or "").strip() == (series_name or "").strip():
            return b.block_id
    return None


def _text_trim(s: str) -> str:
    return (s or "").strip()


def _merge_md(*parts: str) -> str:
    return "\n\n".join([p.strip() for p in parts if p and p.strip()])


def render_series_detail(template_dir: Path, model: ModelBundle) -> str:
    """
    Генерирует по ДВЕ A4-страницы на каждую серию:
      - Страница 1: Геро-изображение + ОПИСАНИЕ (summary_md)
      - Страница 2: (повтор картинки поменьше) + КОНСТРУКЦИЯ (construction_md) + ПРЕИМУЩЕСТВА (features)
    Примечания:
      - якоря: id="sec-{series_block_id}-p1" и "-p2"
      - если hero.photo нет — выводим заглушку
      - features берём из series.features (icon,text), рендерим как маркированный список
    """
    items: List[Dict[str, Any]] = []

    for sec in (model.sections or []):
        for ser in (sec.series or []):
            title = ser.name or ser.code or "Серия"
            sbid = _series_block_id(model, title) or uuid.uuid4().hex[:8]
            hero = (ser.hero.photo or "").strip()

            # Тексты
            description = _text_trim(ser.summary_md)
            construction = _text_trim(ser.construction_md)
            features = _text_trim(ser.features)

            items.append({
                "anchor_p1": f"sec-{sbid}-p1",
                "anchor_p2": f"sec-{sbid}-p2",
                "title": title,
                "hero": hero,
                "description": description,
                "construction": construction,
                "features": features,
                "brand": model.settings.get("theme_color", "#E53935"),
            })

    return render_fragment(template_dir, "series_detail.html.j2", {"items": items})
