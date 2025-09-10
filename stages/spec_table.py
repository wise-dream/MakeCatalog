# stages/spec_table.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
import math

from core.models import ModelBundle, Block
from core.render import render_fragment


# ----------------- helpers -----------------
def _clean_nan(v: Any, default: Optional[str] = None):
    if isinstance(v, float) and math.isnan(v):
        return default
    return v

def _get_param(b: Block, settings, key: str, default: Any = None) -> Any:
    """
    Приоритет: b.params[key] -> Settings[key] -> default.
    """
    if isinstance(b.params, dict) and key in b.params and b.params[key] not in (None, ""):
        return b.params[key]
    val = settings.get(key, "")
    if val != "":
        return val
    return default

def _price_fmt(value: Optional[float], currency: str, pattern: Optional[str]) -> str:
    if value is None:
        return ""
    s = f"{int(value):,}".replace(",", " ")
    if pattern:
        # пример: "### ### ₸"
        return pattern.replace("### ### ₸", f"{s} ₸").replace("### ###", s)
    # дефолт — просто число и валюта
    return f"{s} {currency}" if currency else s

def _build_rows_from_groups(groups: List[Dict[str, Any]], group_headers: bool) -> List[Dict[str, Any]]:
    """
    Ожидает структуру как в json_loader → b.params['attributes']:
    [
      {"group": "Основные", "items":[{"name":"...", "value": ..., "unit":"..."}, ...]},
      ...
    ]
    Возвращает плоский список:
      - строки-группы с ключом _is_group=True
      - обычные строки с attr_name/value/unit
    Порядок сохраняется как в исходном JSON.
    """
    rows: List[Dict[str, Any]] = []
    for g in (groups or []):
        gname = (g.get("group") or "").strip()
        items = g.get("items") or []
        if group_headers and gname:
            rows.append({"_is_group": True, "group": gname})
        for it in items:
            rows.append({
                "_is_group": False,
                "attr_name": (it.get("name") or "").strip(),
                "value": it.get("value", ""),
                "unit": (it.get("unit") or "") or "",
            })
    return rows

def _first_sku_from(b: Block) -> Optional[str]:
    if b.sku_list:
        items = [x.strip() for x in str(b.sku_list).split(",") if x and str(x).strip()]
        return items[0] if items else None
    return None


# ----------------- main API -----------------
def generate_spec_table_for_block(template_dir: Path, model: ModelBundle, b: Block) -> str:
    """
    Рендер одного блока spec_table.
    Источник данных — b.params, которые заполняет json_loader:
      - attributes: список групп с items
      - image, description_md, price, currency, unit, media_refs и т.п.
    """
    assert str(b.type).lower() == "spec_table", "generate_spec_table_for_block called for non-spec_table"

    settings = model.settings
    params: Dict[str, Any] = b.params or {}

    # SKU (информативно; атрибуты уже в params)
    sku = _first_sku_from(b)

    # опции отображения
    group_headers = bool(_get_param(b, settings, "group_headers", True))
    price_pattern = _get_param(b, settings, "price_format", None)
    currency = params.get("currency") or settings.get("currency", "")

    # строки таблицы характеристик
    rows = _build_rows_from_groups(params.get("attributes") or [], group_headers)

    # форматированная цена
    price_fmt = _price_fmt(params.get("price"), currency, price_pattern)

    # якорь для содержания
    anchor = f"sec-{b.block_id}"

    # карточка продукта (модели)
    product_ctx = {
        "sku": sku or "",
        "name": b.title or "",
        "image": _clean_nan(params.get("image"), None),
        "brand": None,
        "unit": _clean_nan(params.get("unit"), None),
        "price_fmt": price_fmt,
        "description": _clean_nan(params.get("description_md"), None),
    }

    ctx: Dict[str, Any] = {
        "page_break_before": bool(b.page_break_before),
        "title": b.title or "",
        "anchor": anchor,
        "product": product_ctx,
        "rows": rows,
        "brand_color": settings.get("theme_color", "#E53935"),
    }

    return render_fragment(template_dir, "spec_table.html.j2", ctx)


def render_all_spec_tables(template_dir: Path, model: ModelBundle) -> List[str]:
    """
    Пробегает по всем блокам и рендерит только spec_table.
    """
    out: List[str] = []
    for b in model.blocks:
        if str(b.type).lower() == "spec_table":
            out.append(generate_spec_table_for_block(template_dir, model, b))
    return out
