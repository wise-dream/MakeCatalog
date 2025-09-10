#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from pathlib import Path


def html_to_pdf(html: str, out_pdf_path: str, base_url: str) -> None:
    """
    WeasyPrint: HTML → PDF.
    base_url = file:// URI каталога, откуда резолвятся относительные пути (например 'file:///.../output/').
    """
    from weasyprint import HTML, CSS

    HTML(string=html, base_url=base_url).write_pdf(
        out_pdf_path,
        stylesheets=[CSS(string="")]
    )


def html_to_pdf_chromium(html_path: str, out_pdf_path: str) -> None:
    """
    Chromium/Playwright: ждём, пока Paged.js дорендерит (window.PAGED_DONE или событие pagedjs:rendered),
    затем печать PDF.

    Требуется:
      pip install playwright
      playwright install chromium
    """
    from playwright.sync_api import sync_playwright

    html_uri = Path(html_path).resolve().as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Paged.js считает пагинацию в screen-режиме
        page.emulate_media(media="screen")

        # Загружаем локальный HTML
        page.goto(html_uri, wait_until="load")
        page.wait_for_load_state("load")

        # Ждём окончания работы Paged.js
        try:
            page.wait_for_function("() => window.PAGED_DONE === true", timeout=20000)
        except Exception:
            # fallback: ждём событие pagedjs:rendered
            page.evaluate(
                """
                () => new Promise((resolve) => {
                  if (typeof window !== 'undefined' && window.PAGED_DONE === true) {
                    resolve(true); return;
                  }
                  const done = () => resolve(true);
                  document.addEventListener('pagedjs:rendered', done, { once: true });
                  setTimeout(done, 10000); // safety timeout
                })
                """
            )

        # Печатаем PDF
        page.pdf(
            path=out_pdf_path,
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "14mm", "right": "14mm", "bottom": "16mm", "left": "14mm"},
        )

        browser.close()
