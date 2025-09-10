# stages/toc.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.render import render_fragment
from core.models import ModelBundle, Block


def _want_in_toc(b: Block) -> Optional[bool]:
    """Если явно указано show_in_toc в params → True/False, иначе None."""
    if isinstance(b.params, dict) and "show_in_toc" in b.params:
        v = str(b.params.get("show_in_toc")).strip().lower()
        if v in ("yes", "true", "1", "да"):
            return True
        if v in ("no", "false", "0", "нет"):
            return False
    return None


def _parents_chain(model: ModelBundle, b: Block) -> List[Block]:
    """
    Поднимаемся по parent_id (или аналогам), формируя цепочку предков.
    Поддерживаем несколько возможных полей, чтобы не зависеть от конкретной реализации.
    """
    idx: Dict[Any, Block] = getattr(model, "block_index", None) or {
        getattr(x, "block_id"): x for x in model.blocks
    }

    chain: List[Block] = []
    # Возможные имена поля родителя
    parent_keys = ("parent_id", "parent", "parent_block_id", "parent_block")

    def _get_parent_id(obj: Block) -> Optional[Any]:
        for k in parent_keys:
            if hasattr(obj, k):
                val = getattr(obj, k)
                # если поле само объект — попробуем взять его id
                if isinstance(val, Block):
                    return getattr(val, "block_id", None)
                return val
        return None

    cur = b
    guard = 0
    while guard < 100:
        guard += 1
        pid = _get_parent_id(cur)
        if pid is None:
            break
        parent = idx.get(pid)
        if parent is None:
            break
        chain.append(parent)
        cur = parent
    return chain


def _infer_section_level_by_hierarchy(model: ModelBundle, b: Block) -> int:
    """
    TOC-уровень для section_heading по ИЕРАРХИИ:
      - считаем количество предков с type == "section_heading"
      - 0 предков → уровень 1 (тип оборудования)
      - ≥1 предок → уровень 2 (серия)
      - глубину >2 схлопываем до 2 (в TOC у нас два уровня)
    """
    if str(getattr(b, "type", "")).lower() != "section_heading":
        # Для не section_heading уровень по иерархии не нужен
        return 1

    chain = _parents_chain(model, b)
    section_ancestors = sum(1 for p in chain if str(getattr(p, "type", "")).lower() == "section_heading")
    if section_ancestors <= 0:
        return 1
    # Если есть хотя бы один раздел-предок — это серия (уровень 2)
    return 2


def _infer_section_level(model: ModelBundle, b: Block) -> int:
    """
    Порядок определения уровня:
      1) Явное params.toc_level = 1|2
      2) По иерархии (число предков section_heading)
      3) Фоллбек: 1
    """
    params = b.params if isinstance(b.params, dict) else {}

    # 1) Явный уровень
    lvl = params.get("toc_level")
    if lvl is not None:
        try:
            lvl_int = int(lvl)
            if lvl_int in (1, 2):
                return lvl_int
        except Exception:
            pass

    # 2) Иерархия
    return _infer_section_level_by_hierarchy(model, b)


def generate_toc(template_dir: Path, model: ModelBundle) -> str:
    """
    Содержание:
      - Уровень 1: тип оборудования (верхние разделы)
      - Уровень 2: серии (внутри текущего типа)
      - Таблицы моделей (spec_table) скрыты по умолчанию; можно включить точечно через params.show_in_toc = true.
    Анкоры: id="sec-{{ b.block_id }}" у целевых блоков.
    """
    entries: List[Dict[str, Any]] = []
    current_type_idx: Optional[int] = None  # индекс последнего L1 (тип)

    for b in model.blocks:
        btype = str(getattr(b, "type", "")).lower()
        explicit = _want_in_toc(b)

        if btype == "section_heading":
            # Решаем уровень по иерархии (или явному toc_level)
            level = _infer_section_level(model, b)

            # Пропуск всего блока, если явно выключили
            if explicit is False:
                if level == 1:
                    current_type_idx = None
                continue

            title = getattr(b, "title", None) or getattr(b, "category_id", None)
            if not title:
                if level == 1:
                    current_type_idx = None
                continue

            if level == 1:
                # Новый тип оборудования — верхний уровень
                entries.append({
                    "level": 1,
                    "title": title,
                    "anchor": f"sec-{b.block_id}",
                    "children": [],
                })
                current_type_idx = len(entries) - 1
            else:
                # Серия — второй уровень внутри текущего типа; если типа нет — делаем плоско
                child = {
                    "level": 2,
                    "title": title,
                    "anchor": f"sec-{b.block_id}",
                }
                if current_type_idx is not None:
                    entries[current_type_idx]["children"].append(child)
                else:
                    entries.append(child)

        elif btype == "spec_table":
            # Страницы моделей по умолчанию НЕ включаем, чтобы TOC был «типы → серии».
            # Включение возможно ТОЛЬКО при явном show_in_toc = true (например, для сводных табличных страниц серии).
            include = explicit is True
            if not include:
                continue

            title = getattr(b, "title", None) or getattr(b, "category_id", None)
            if not title and getattr(b, "sku_list", None):
                # fallback: если есть sku_list, возьмём первый SKU как заголовок (на случай ручного включения)
                try:
                    title = b.sku_list.split(",")[0].strip()
                except Exception:
                    pass
            if not title:
                continue

            child = {
                "level": 2,  # показываем как подпункт текущего типа
                "title": title,
                "anchor": f"sec-{b.block_id}",
            }
            if current_type_idx is not None:
                entries[current_type_idx]["children"].append(child)
            else:
                entries.append(child)

        else:
            # Прочие блоки добавляем в TOC только при явном show_in_toc = true.
            if explicit:
                title = getattr(b, "title", None) or getattr(b, "category_id", None)
                if not title:
                    continue
                # Определим уровень для прочих блоков: используем те же правила (можно задать params.toc_level)
                level = _infer_section_level(model, b) if str(getattr(b, "type", "")).lower() == "section_heading" else (
                    int(b.params.get("toc_level")) if isinstance(b.params, dict) and str(b.params.get("toc_level", "")).isdigit() else 1
                )
                if level == 1:
                    entries.append({
                        "level": 1,
                        "title": title,
                        "anchor": f"sec-{b.block_id}",
                        "children": [],
                    })
                    current_type_idx = len(entries) - 1
                else:
                    child = {
                        "level": 2,
                        "title": title,
                        "anchor": f"sec-{b.block_id}",
                    }
                    if current_type_idx is not None:
                        entries[current_type_idx]["children"].append(child)
                    else:
                        entries.append(child)

    return render_fragment(template_dir, "toc.html.j2", {"entries": entries})
