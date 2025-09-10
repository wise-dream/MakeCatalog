# core/json_loader.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import json
import re
import uuid

from .models import (
    Catalog,
    ModelBundle,
    Block,
)

_ID_SAFE = re.compile(r"[^a-zA-Z0-9_-]+")

def _slug(s: str) -> str:
    s = (s or "").strip().replace(" ", "-")
    s = _ID_SAFE.sub("-", s)
    if not s:
        s = uuid.uuid4().hex[:8]
    return s[:64]

def _new_block_id(prefix: str, *parts: str) -> str:
    base = "-".join([prefix] + [p for p in parts if p])
    return f"{_slug(base)}-{uuid.uuid4().hex[:6]}"

def _as_str(v: Any) -> str:
    return "" if v is None else str(v)

def load_catalog(path: Path) -> ModelBundle:
    """
    Загружает НОВЫЙ JSON-формат (settings/sections/series/models/...),
    собирает ModelBundle с блоками:
      - cover, toc, backcover
      - section_heading (L1: тип), section_heading (L2: серия)
      - text_block / image_full / curve / серийные таблицы
    ВНИМАНИЕ: страницы моделей (spec_table) НЕ создаются, если не включено settings.generate_model_pages == "yes".
    """
    if path.suffix.lower() != ".json":
        raise ValueError("Ожидался файл .json с каталогом")

    data: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    catalog: Catalog = Catalog.from_dict(data)

    blocks: List[Block] = []
    order = 0

    # ----- Обложка -----
    blocks.append(Block(
        block_id=_new_block_id("cover", "front"),
        type="cover",
        title=None, subtitle=None,
        category_id=None, sku_list=None, layout=None, columns=None,
        params={"page": "cover"},
        page_break_before=False, show_in_toc=False, order=order, parent_id=None,
    ))
    order += 10

    # ----- TOC -----
    blocks.append(Block(
        block_id=_new_block_id("toc", "contents"),
        type="toc",
        title="Содержание", subtitle=None,
        category_id=None, sku_list=None, layout=None, columns=None,
        params={"page": "toc", "page_break_before": True},
        page_break_before=True, show_in_toc=False, order=order, parent_id=None,
    ))
    order += 10

    # Флаг генерации страниц моделей
    gen_models = (catalog.settings.get("generate_model_pages", "no").lower() in ("yes", "true", "1", "да"))

    # ----- Разделы → Серии → Контент -----
    for sec in catalog.sections:
        sec_title = sec.title or sec.code or "Раздел"
        sec_block_id = _new_block_id("sec", sec.code or sec.title)

        # L1 заголовок (тип)
        blocks.append(Block(
            block_id=sec_block_id,
            type="section_heading",
            title=sec_title, subtitle=None,
            category_id=None, sku_list=None, layout=None, columns=None,
            params={"toc_level": 1},
            page_break_before=True, show_in_toc=True, order=order, parent_id=None,
        ))
        order += 10

        # Введение раздела
        if sec.intro_md:
            blocks.append(Block(
                block_id=_new_block_id("txt", "intro", sec.code or sec.title),
                type="text_block",
                title="Введение", subtitle=None,
                category_id=None, sku_list=None, layout=None, columns=None,
                params={"text_md": sec.intro_md},
                page_break_before=False, show_in_toc=False, order=order, parent_id=sec_block_id,
            ))
            order += 10

        for ser in sec.series:
            ser_name = ser.name or ser.code or "Серия"
            ser_block_id = _new_block_id("ser", ser.code or ser.name)

            # L2 заголовок (серия)
            blocks.append(Block(
                block_id=ser_block_id,
                type="section_heading",
                title=ser_name, subtitle=None,
                category_id=None, sku_list=None, layout=None, columns=None,
                params={"toc_level": 2},
                page_break_before=True, show_in_toc=True, order=order, parent_id=sec_block_id,
            ))
            order += 10

            # Hero
            if ser.hero and (ser.hero.photo or "").strip():
                blocks.append(Block(
                    block_id=_new_block_id("img", "hero", ser.code or ser.name),
                    type="image_full",
                    title=ser_name, subtitle=None,
                    category_id=None, sku_list=None, layout=None, columns=None,
                    params={"media": ser.hero.photo, "caption": ser_name},
                    page_break_before=False, show_in_toc=False, order=order, parent_id=ser_block_id,
                ))
                order += 10

            # Описание серии
            md_parts: List[str] = []
            if (ser.summary_md or "").strip():
                md_parts.append(ser.summary_md.strip())
            if (ser.construction_md or "").strip():
                md_parts.append("**Конструкция**\n" + ser.construction_md.strip())
            if md_parts:
                blocks.append(Block(
                    block_id=_new_block_id("txt", "series", ser.code or ser.name),
                    type="text_block",
                    title="Описание серии", subtitle=None,
                    category_id=None, sku_list=None, layout=None, columns=None,
                    params={"text_md": "\n\n".join(md_parts)},
                    page_break_before=False, show_in_toc=False, order=order, parent_id=ser_block_id,
                ))
                order += 10

            # Серийные таблицы
            for tbl in ser.tables:
                if not (tbl.columns and tbl.rows):
                    continue
                headers = [(_as_str(c.title or c.key)) for c in tbl.columns]
                keys = [(_as_str(c.key)) for c in tbl.columns]
                md = "| " + " | ".join(headers) + " |\n"
                md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                for row in tbl.rows:
                    md += "| " + " | ".join(_as_str(row.get(k, "")) for k in keys) + " |\n"
                if (tbl.notes_md or "").strip():
                    md += "\n" + tbl.notes_md.strip()

                blocks.append(Block(
                    block_id=_new_block_id("tbl", tbl.type or "table"),
                    type="text_block",
                    title=tbl.title or "Таблица", subtitle=None,
                    category_id=None, sku_list=None, layout=None, columns=None,
                    params={"text_md": md},
                    page_break_before=False, show_in_toc=False, order=order, parent_id=ser_block_id,
                ))
                order += 10

            # Медиа
            for m in ser.media:
                if not (m.file or "").strip():
                    continue
                if str(m.type) == "curve" and m.dataset:
                    blocks.append(Block(
                        block_id=_new_block_id("curve", m.id or ser.code or ser.name),
                        type="curve",
                        title=m.caption or "Аэродинамическая характеристика",
                        subtitle=None, category_id=None, sku_list=None,
                        layout=None, columns=None,
                        params={
                            "dataset": {
                                "x_unit": m.dataset.x_unit,
                                "y_unit": m.dataset.y_unit,
                                "series": [
                                    {"label": s.label, "points": s.points}
                                    for s in m.dataset.series
                                ],
                            }
                        },
                        page_break_before=False, show_in_toc=False, order=order, parent_id=ser_block_id,
                    ))
                else:
                    blocks.append(Block(
                        block_id=_new_block_id("img", m.id or ser.code or ser.name),
                        type="image_full",
                        title=m.caption or "Иллюстрация",
                        subtitle=None, category_id=None, sku_list=None,
                        layout=None, columns=None,
                        params={"media": m.file, "caption": m.caption},
                        page_break_before=False, show_in_toc=False, order=order, parent_id=ser_block_id,
                    ))
                order += 10

            # СТРАНИЦЫ МОДЕЛЕЙ: создаём ТОЛЬКО если явно включено
            if gen_models:
                for mdl in ser.models:
                    sku = (mdl.sku or "").strip()
                    if not sku:
                        continue
                    attr_payload: List[Dict[str, Any]] = []
                    for g in mdl.attributes:
                        attr_payload.append({
                            "group": g.group,
                            "items": [
                                {"name": it.name, "value": it.value, "unit": it.unit}
                                for it in g.items
                            ],
                        })
                    blocks.append(Block(
                        block_id=_new_block_id("spec", sku),
                        type="spec_table",
                        title=mdl.name or sku, subtitle=None, category_id=None,
                        sku_list=sku, layout="grid-2", columns=2,
                        params={
                            "page_break_before": True,
                            "group_headers": True,
                            "attributes": attr_payload,
                            "image": (mdl.image or None),
                            "description_md": (mdl.description_md or ""),
                            "price": mdl.price,
                            "currency": mdl.currency or catalog.settings.currency,
                            "unit": mdl.unit,
                            "media_refs": mdl.media_refs,
                        },
                        page_break_before=True,
                        show_in_toc=False,
                        order=order,
                        parent_id=ser_block_id,
                    ))
                    order += 10

    # ----- Задняя обложка -----
    blocks.append(Block(
        block_id=_new_block_id("cover", "back"),
        type="backcover",
        title="Контакты", subtitle=None,
        category_id=None, sku_list=None, layout=None, columns=None,
        params={"page": "backcover"},
        page_break_before=True, show_in_toc=False, order=order, parent_id=None,
    ))
    order += 10

    mb = ModelBundle(
        settings=catalog.settings,
        sections=catalog.sections,
        blocks=sorted(blocks, key=lambda b: b.order),
        block_index={},
    )
    mb.rebuild_index()
    return mb
