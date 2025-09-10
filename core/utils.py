from __future__ import annotations
from typing import Any, List, Optional

def clean_nan(x: Any) -> Any:
    import math
    return None if isinstance(x, float) and math.isnan(x) else x

def split_csv(s: Optional[str]) -> List[str]:
    if not s: return []
    return [x.strip() for x in str(s).split(",") if x.strip()]

def price_fmt(value: Optional[float], currency: str, pattern: Optional[str]) -> str:
    if value is None: return ""
    s = f"{int(value):,}".replace(",", " ")
    if pattern and "₸" in pattern: return pattern.replace("### ### ₸", f"{s} ₸")
    return f"{s} {currency}"

def md_basic(text: str) -> str:
    if not text: return ""
    import html
    t = html.escape(text).replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("**", "\x00")
    out = []
    for i, p in enumerate(t.split("\x00")):
        out.append(f"<strong>{p}</strong>" if i % 2 else p)
    return "".join(out).replace("\n", "<br>")
