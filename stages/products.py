# stages/products.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import re
import uuid

from core.models import ModelBundle, Table
from core.render import render_fragment

# =========================
# Helpers
# =========================

_ID_SAFE = re.compile(r"[^a-zA-Z0-9_-]+")


def _slug(s: str) -> str:
    s = (s or "").strip().replace(" ", "-")
    s = _ID_SAFE.sub("-", s)
    if not s:
        s = uuid.uuid4().hex[:8]
    return s[:64]


def _find_series_block_anchor(model: ModelBundle, series_title: str) -> str:
    """
    Ищем anchor для серии по соответствующему section_heading (L2).
    Совпадение по заголовку (title == series.name). Если не нашли — генерируем.
    """
    for b in model.blocks:
        if str(getattr(b, "type", "")).lower() != "section_heading":
            continue
        params = b.params or {}
        lvl = params.get("toc_level")
        try:
            lvl = int(lvl)
        except Exception:
            lvl = None
        if lvl == 2 and (b.title or "").strip() == (series_title or "").strip():
            return f"sec-{b.block_id}"
    # резервный якорь (если заголовочного блока нет/иначе назван)
    return f"sec-{_slug('series-' + (series_title or ''))}"


def _table_to_ctx(tbl: Table) -> Dict[str, Any]:
    """
    Конверсия core.models.Table → универсальный контекст для шаблона.
    Новый формат: columns[{key,title}], rows=[{key:value,...}]
    (Обновлённый products.html.j2 умеет и старый, но мы отдаём новый.)
    """
    cols = [{"key": c.key, "title": (c.title or c.key)} for c in (tbl.columns or [])]
    row_dicts: List[Dict[str, Any]] = []
    keys = [c["key"] for c in cols]
    for r in (tbl.rows or []):
        # r может быть dict (современно) или list (наследие)
        if isinstance(r, dict):
            row_dicts.append({k: r.get(k, "") for k in keys})
        else:
            # список значений — сопоставим по порядку колонок
            row = {}
            for i, k in enumerate(keys):
                row[k] = r[i] if i < len(r) else ""
            row_dicts.append(row)

    return {
        "type": tbl.type,
        "title": tbl.title or "",
        "columns": cols,
        "rows": row_dicts,
        "notes_md": tbl.notes_md or "",
    }


def _series_top_ctx(ser: Any) -> Dict[str, Any]:
    """
    Достаём «шапку серии»: hero (фото/баннер), naming (расшифровка), summary_md.
    Эти поля могут отсутствовать в core.models.Series — тогда просто дефолты.
    """
    hero = {}
    s_hero = getattr(ser, "hero", None) or {}
    hero["photo"] = (s_hero.get("photo") if isinstance(s_hero, dict) else getattr(s_hero, "photo", None)) or ""
    hero["banner_md"] = (s_hero.get("banner_md") if isinstance(s_hero, dict) else getattr(s_hero, "banner_md", None)) or ""

    naming = getattr(ser, "naming", None) or {}
    if not isinstance(naming, dict):
        naming = {
            "code": getattr(naming, "code", ""),
            "pattern": getattr(naming, "pattern", ""),
            "legend": getattr(naming, "legend", []) or [],
        }
    else:
        naming.setdefault("code", "")
        naming.setdefault("pattern", "")
        # гарантируем список
        legend = naming.get("legend") or []
        naming["legend"] = legend

    summary_md = getattr(ser, "summary_md", "") or ""

    return {"hero": hero, "naming": naming, "summary_md": summary_md}


def _series_media_ctx(ser: Any) -> List[Dict[str, Any]]:
    """
    Медиа объектов может не быть. Ожидаем список dict с полями: file, caption, type.
    Ненужные/пустые пропускаем.
    """
    media = getattr(ser, "media", None) or []
    out: List[Dict[str, Any]] = []
    for m in media:
        if not isinstance(m, dict):
            file = getattr(m, "file", "") or ""
            cap = getattr(m, "caption", "") or ""
            typ = getattr(m, "type", "") or ""
        else:
            file = m.get("file", "") or ""
            cap = m.get("caption", "") or ""
            typ = m.get("type", "") or ""
        if not file:
            continue
        out.append({"file": file, "caption": cap, "type": typ})
    return out


# =========================
# Main entry
# =========================

def generate_products(template_dir: Path, model: ModelBundle) -> str:
    """
    Рендер «серий и их таблиц»: продукт = серия, внутри — таблицы характеристик,
    верхний пояс (фото + расшифровка), затем сетка медиа.
    Возвращает один фрагмент HTML, построенный по шаблону products.html.j2.
    """
    series_groups: List[Dict[str, Any]] = []

    for sec in (model.sections or []):
        sec_title = (sec.title or "").strip()
        for ser in (sec.series or []):
            series_title = (getattr(ser, "name", None) or getattr(ser, "code", None) or "").strip()
            if not series_title:
                continue

            anchor = _find_series_block_anchor(model, series_title)

            # Таблицы серии
            tables_ctx: List[Dict[str, Any]] = []
            for t in (getattr(ser, "tables", None) or []):
                tables_ctx.append(_table_to_ctx(t))

            if not tables_ctx:
                # Если по серии нет таблиц — пропускаем, чтобы не плодить пустые полосы.
                continue

            top = _series_top_ctx(ser)
            media = _series_media_ctx(ser)

            series_groups.append({
                # Для шапки
                "title": getattr(ser, "name", None) or getattr(ser, "code", None) or "Серия",
                "name": getattr(ser, "name", None) or getattr(ser, "code", None) or "Серия",
                "code": getattr(ser, "code", None) or "",
                "subtitle": sec_title,
                "anchor": anchor,
                "page_break_before": True,

                # Верхний блок
                "hero": top["hero"],
                "naming": top["naming"],
                "summary_md": top["summary_md"],

                # Таблицы
                "tables": tables_ctx,

                # Медиа
                "media": media,
            })

    ctx = {
        "series_groups": series_groups,
        "settings": model.settings,
    }

    return render_fragment(template_dir, "products.html.j2", ctx)
