# stages/section_covers.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import os
import re
import urllib.parse

from core.models import ModelBundle, Block, Section
from core.render import render_fragment


def _is_l1_section(b: Block) -> bool:
    if str(getattr(b, "type", "")).lower() != "section_heading":
        return False
    params = b.params or {}
    try:
        lvl = int(params.get("toc_level"))
    except Exception:
        lvl = None
    return lvl == 1


def _resolve_image_src(sec: Section, settings) -> str:
    """
    Логика выбора относительного src для изображения:
      1) settings.section_cover_map[sec.code] (если есть)
      2) settings.section_cover_pattern (по умолчанию "images/{code}.jpg")
      3) если нет кода — ASCII-слаг из title
    Возвращаем СТРОГО относительный путь (без "output/"),
    чтобы <base href=".../output/"> корректно склеил в итоговый URL.
    """
    # 1) словарь-оверрайд
    cov_map = getattr(settings, "section_cover_map", None)
    if isinstance(cov_map, dict):
        key = (sec.code or "").strip()
        if key and key in cov_map and cov_map[key]:
            return str(cov_map[key])

    # 2) паттерн
    code = (sec.code or "").strip()
    if not code:
        # ASCII-слаг из названия (на случай отсутствия code)
        t = (sec.title or "section").strip().replace(" ", "-")
        code = re.sub(r"[^a-zA-Z0-9_-]+", "-", t).strip("-") or "section"

    pattern = settings.get("section_cover_pattern", "images/{code}.jpg")
    return pattern.replace("{code}", code).replace("{title}", sec.title or "")


def _abs_fs_path(rel_src: str, assets_base: str, cwd: Path) -> Path:
    """
    Пробуем получить абсолютный файловый путь для проверки наличия файла.
    Поддержка:
      - assets_base = "output/" → cwd/"output"/rel_src
      - assets_base = "file:///abs/output/" → /abs/output/rel_src
      - assets_base = "" → cwd/rel_src
    """
    if assets_base and assets_base.startswith("file://"):
        # file:// URL → парсим и склеиваем
        parsed = urllib.parse.urlparse(assets_base)
        base_path = Path(urllib.parse.unquote(parsed.path))
        return (base_path / rel_src).resolve()
    if assets_base:
        # относительный базовый путь
        return (cwd / assets_base / rel_src).resolve()
    return (cwd / rel_src).resolve()


def _find_section_for_block(model: ModelBundle, b: Block) -> Optional[Section]:
    title_key = (b.title or "").strip().lower()
    for s in model.sections or []:
        if (s.title or "").strip().lower() == title_key:
            return s
        if (s.code or "").strip().lower() == title_key:
            return s
    for s in model.sections or []:
        if s.code and s.code.strip().lower() in title_key:
            return s
    return None


def _first_line_md(text: str, max_len: int = 180) -> str:
    if not text:
        return ""
    t = text.strip().splitlines()[0].strip()
    # уберём простейшую разметку
    t = re.sub(r"(\*\*|__|`)+", "", t)
    if len(t) > max_len:
        t = t[: max_len - 1].rstrip() + "…"
    return t


def render_section_covers(template_dir: Path, model: ModelBundle) -> str:
    """
    Рендерит полноэкранные «открывашки» для L1: фон как <img> (object-fit:cover) + текст.
    Плюс диагностика пути: если файл не найден — выводим плашку с rel и abs путями.
    """
    covers: List[Dict[str, Any]] = []

    align = (model.settings.get("section_cover_title_align", "left") or "left").lower()
    pos = (model.settings.get("section_cover_title_pos", "bottom-left") or "bottom-left").lower()
    text_color = model.settings.get("section_cover_text_color", "#fff") or "#fff"
    use_shadow = (model.settings.get("section_cover_shadow", "yes").lower() in ("yes", "true", "1", "да"))
    use_gradient = (model.settings.get("section_cover_gradient", "yes").lower() in ("yes", "true", "1", "да"))

    assets_base = model.settings.get("assets_base", "")  # ожидаем "output/" или file://...
    cwd = Path.cwd()

    for b in model.blocks:
        if not _is_l1_section(b):
            continue

        sec = _find_section_for_block(model, b) or Section(code="", title=(b.title or "Раздел"), intro_md="")
        rel_src = _resolve_image_src(sec, model.settings)
        abs_path = _abs_fs_path(rel_src, assets_base, cwd)
        exists = abs_path.exists()

        covers.append({
            "anchor": f"sec-{b.block_id}",
            "image": rel_src,              # ПУБЛИЧНЫЙ (через <base>) путь для <img>
            "image_abs": str(abs_path),    # Для диагностики
            "image_exists": exists,        # Для ветки в шаблоне
            "title": sec.title or b.title or "Раздел",
            "subtitle": _first_line_md(getattr(sec, "intro_md", "")),
            "align": align,
            "pos": pos,
            "text_color": text_color,
            "use_shadow": use_shadow,
            "use_gradient": use_gradient,
            "brand": model.settings.get("theme_color", "#E53935"),
        })

    return render_fragment(template_dir, "section_cover.html.j2", {"covers": covers})
