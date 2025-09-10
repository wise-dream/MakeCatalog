from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

def render_fragment(template_dir: Path, template: str, ctx: Dict[str, Any]) -> str:
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=select_autoescape(["html","xml"]))
    return env.get_template(template).render(**ctx)

def assemble_document(template_dir: Path, fragments: List[str], settings: Dict[str, Any]) -> str:
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=select_autoescape(["html","xml"]))
    base = env.get_template("base.html.j2")
    return base.render(fragments=fragments, settings=settings)
