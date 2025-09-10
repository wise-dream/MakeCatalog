#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from pathlib import Path
import argparse
from typing import Any, Iterable

from core.json_loader import load_catalog  # <-- JSON формат
from core.render import assemble_document
from core.export import html_to_pdf, html_to_pdf_chromium

from stages.cover import generate_cover
from stages.toc import generate_toc
from stages.products import generate_products
from stages.backcover import generate_backcover
from stages.spec_table import render_all_spec_tables  # если используешь spec-страницы
from stages.section_cover import render_section_covers
from stages.series_detail import render_series_detail


# -----------------------------------------------------------------------------
# ПРОКСИ-ОБЪЕКТЫ: безопасно «сужаем» модель/раздел без изменения исходных типов
# -----------------------------------------------------------------------------
class SectionProxy:
    """Обёртка над исходным разделом, подменяющая только .series на подмножество."""
    __slots__ = ("_base", "series")

    def __init__(self, base_section: Any, series_subset: Iterable[Any]):
        self._base = base_section
        # именно список (многие шаблоны делают len()/итерацию)
        self.series = list(series_subset)

    def __getattr__(self, name: str) -> Any:
        # Все остальные атрибуты берём у исходного раздела (title, code, intro_md, accessories, etc.)
        return getattr(self._base, name)


class ModelProxy:
    """Обёртка над исходной моделью, подменяющая только .sections на переданный список."""
    __slots__ = ("_base", "settings", "sections")

    def __init__(self, base_model: Any, sections_subset: Iterable[Any]):
        self._base = base_model
        # settings оставляем тем же объектом, что и в исходной модели (там могут быть .get/.attrs)
        self.settings = base_model.settings
        # список секций для рендера (одна секция или несколько)
        self.sections = list(sections_subset)

    def __getattr__(self, name: str) -> Any:
        # Прозрачная прокси: всё, чего нет у нас, читаем из исходной модели
        return getattr(self._base, name)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description="Пайплайн каталога → HTML/PDF A4 (JSON источник)")
    p.add_argument("json", help="Путь к JSON (например data/catalog.json)")
    p.add_argument("--out-html", default="output/catalog.html", help="HTML вывод")
    p.add_argument("--out-pdf", default="output/catalog.pdf", help="PDF вывод")
    p.add_argument("--templates", default="templates", help="Папка с шаблонами")
    p.add_argument("--engine", choices=["weasyprint", "chromium"], default="chromium",
                   help="Движок PDF: chromium (по умолчанию) или weasyprint")
    p.add_argument("--no-cover", action="store_true",
                   help="Не добавлять обложку и не сбрасывать нумерацию после неё")
    return p.parse_args()


def main():
    args = parse_args()
    base = Path.cwd()
    templates = (base / args.templates).resolve()

    out_html = (base / args.out_html).resolve()
    out_pdf = (base / args.out_pdf).resolve() if args.out_pdf else None

    model = load_catalog(Path(args.json).resolve())

    # База ассетов = папка, где будет лежать HTML + images/
    assets_root = out_html.parent
    assets_root.mkdir(parents=True, exist_ok=True)
    assets_base_uri = assets_root.as_uri() + "/"

    # Прокидываем базу и флаги в Settings (оставляем исходный тип settings как есть)
    # Во многих проектах settings поддерживает и attr-доступ, и .get(); не меняем это.
    setattr(model.settings, "assets_base", assets_base_uri)
    setattr(model.settings, "use_pagedjs", "yes" if args.engine == "chromium" else "no")
    setattr(model.settings, "has_cover", "no" if args.no_cover else "yes")

    # Этапы (фрагменты HTML)
    frags: list[str] = []

    # 1) Обложка
    if not args.no_cover:
        frags.append(generate_cover(templates, model))

    # 2) Оглавление — глобально по всей модели
    frags.append(generate_toc(templates, model))

    # 3) По разделам → по сериям, с нужной очерёдностью:
    #    (крышка раздела) → (описание серии → продукты серии → спеки серии) × N
    for section in getattr(model, "sections", []) or []:
        # Крышка ТЕКУЩЕГО раздела (подсовываем модель только с этой секцией)
        frags.append(render_section_covers(templates, ModelProxy(model, [section])))

        # Далее — по сериям этого раздела
        for series in getattr(section, "series", []) or []:
            # Модель, в которой один раздел — SectionProxy с одной серией
            one_series_model = ModelProxy(model, [SectionProxy(section, [series])])

            # Описание/деталка серии
            frags.append(render_series_detail(templates, one_series_model))

            # Продуктовые блоки ТОЛЬКО этой серии (карточки, таблицы, кривые и т.д.)
            frags.append(generate_products(templates, one_series_model))

            # Отдельные спецификации по моделям этой серии (если используют spec-страницы)
            spec_frags = render_all_spec_tables(templates, one_series_model)
            if isinstance(spec_frags, list):
                frags.extend(spec_frags)
            elif spec_frags:
                frags.append(spec_frags)

    # 4) Задняя обложка
    if not args.no_cover:
        frags.append(generate_backcover(templates, model))

    # 5) Сборка HTML
    html = assemble_document(templates, frags, settings=model.settings)
    out_html.write_text(html, encoding="utf-8")
    print(str(out_html))

    # 6) PDF
    if out_pdf:
        if args.engine == "weasyprint":
            html_to_pdf(html, str(out_pdf), base_url=assets_base_uri)
        else:
            # Chromium (Playwright) + Paged.js → корректные номера, переносы, full-bleed
            html_to_pdf_chromium(str(out_html), str(out_pdf))
        print(str(out_pdf))


if __name__ == "__main__":
    main()
