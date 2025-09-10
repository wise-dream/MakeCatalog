# core/models.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Iterable, Literal
from enum import Enum
import re
import uuid


# ==========
# Settings
# ==========

@dataclass
class Company:
    name: str = ""
    address: str = ""
    contacts: str = ""

    @staticmethod
    def from_dict(d: Optional[Dict[str, Any]]) -> Company:
        d = d or {}
        return Company(
            name=str(d.get("name", "") or ""),
            address=str(d.get("address", "") or ""),
            contacts=str(d.get("contacts", "") or ""),
        )


@dataclass
class Settings:
    year: str = ""
    title: str = ""
    theme_color: str = "#E53935"
    currency: str = "₸"
    cover_bg: str = ""
    cover_logo: str = ""
    assets_base: str = ""
    use_pagedjs: str = "yes"
    company: Company = field(default_factory=Company)

    def get(self, key: str, default: str = "") -> str:
        # совместимость с существующими шаблонами
        val = getattr(self, key, None)
        if val is None:
            return default
        return str(val)

    @staticmethod
    def from_dict(d: Optional[Dict[str, Any]]) -> Settings:
        d = d or {}
        return Settings(
            year=str(d.get("year", "") or ""),
            title=str(d.get("title", "") or ""),
            theme_color=str(d.get("theme_color", "#E53935") or "#E53935"),
            currency=str(d.get("currency", "₸") or "₸"),
            cover_bg=str(d.get("cover_bg", "") or ""),
            cover_logo=str(d.get("cover_logo", "") or ""),
            assets_base=str(d.get("assets_base", "") or ""),
            use_pagedjs=str(d.get("use_pagedjs", "yes") or "yes"),
            company=Company.from_dict(d.get("company")),
        )


# ==========
# Tables
# ==========

TableType = Literal["technical", "acoustic", "dimensions", "pricing", "custom"]

@dataclass
class TableColumn:
    key: str
    title: str

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> TableColumn:
        return TableColumn(
            key=str(d.get("key", "") or ""),
            title=str(d.get("title", "") or ""),
        )


@dataclass
class Table:
    type: TableType = "custom"
    title: str = ""
    columns: List[TableColumn] = field(default_factory=list)
    rows: List[Dict[str, Any]] = field(default_factory=list)
    notes_md: str = ""

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> Table:
        cols = [TableColumn.from_dict(c) for c in (d.get("columns") or [])]
        rows = list(d.get("rows") or [])
        return Table(
            type=str(d.get("type", "custom") or "custom"),  # сохраняем как строковый literal
            title=str(d.get("title", "") or ""),
            columns=cols,
            rows=rows,
            notes_md=str(d.get("notes_md", "") or ""),
        )


# ==========
# Media (включая curve)
# ==========

class MediaType(str, Enum):
    photo = "photo"
    drawing = "drawing"
    curve = "curve"
    video = "video"
    doc = "doc"

@dataclass
class CurveSeries:
    label: str
    points: List[Tuple[float, float]]  # [(x, y), ...]

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> CurveSeries:
        raw_pts = d.get("points") or []
        pts: List[Tuple[float, float]] = []
        for p in raw_pts:
            try:
                x, y = p
                pts.append((float(x), float(y)))
            except Exception:
                # пропускаем некорректные точки
                continue
        return CurveSeries(
            label=str(d.get("label", "") or ""),
            points=pts,
        )

@dataclass
class CurveDataset:
    x_unit: str = ""
    y_unit: str = ""
    series: List[CurveSeries] = field(default_factory=list)

    @staticmethod
    def from_dict(d: Optional[Dict[str, Any]]) -> CurveDataset:
        d = d or {}
        return CurveDataset(
            x_unit=str(d.get("x_unit", "") or ""),
            y_unit=str(d.get("y_unit", "") or ""),
            series=[CurveSeries.from_dict(s) for s in (d.get("series") or [])],
        )

@dataclass
class MediaItem:
    id: str
    type: MediaType
    file: str
    caption: str = ""
    dataset: Optional[CurveDataset] = None

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> MediaItem:
        mtype = str(d.get("type", "photo") or "photo")
        dataset = CurveDataset.from_dict(d.get("dataset")) if mtype == "curve" else None
        return MediaItem(
            id=str(d.get("id", "") or ""),
            type=MediaType(mtype),
            file=str(d.get("file", "") or ""),
            caption=str(d.get("caption", "") or ""),
            dataset=dataset,
        )


# ==========
# Features / Hero
# ==========

@dataclass
class Hero:
    photo: str = ""
    banner_md: str = ""

    @staticmethod
    def from_dict(d: Optional[Dict[str, Any]]) -> Hero:
        d = d or {}
        return Hero(
            photo=str(d.get("photo", "") or ""),
            banner_md=str(d.get("banner_md", "") or ""),
        )


# ==========
# Attributes / Model
# ==========

@dataclass
class AttributeItem:
    name: str
    value: Any
    unit: Optional[str] = None

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> AttributeItem:
        return AttributeItem(
            name=str(d.get("name", "") or ""),
            value=d.get("value"),
            unit=(str(d.get("unit")) if d.get("unit") is not None else None),
        )

@dataclass
class AttributeGroup:
    group: str
    items: List[AttributeItem] = field(default_factory=list)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> AttributeGroup:
        return AttributeGroup(
            group=str(d.get("group", "") or ""),
            items=[AttributeItem.from_dict(i) for i in (d.get("items") or [])],
        )

@dataclass
class Model:
    sku: str
    name: str
    price: Optional[float] = None
    currency: Optional[str] = None
    unit: Optional[str] = None
    image: Optional[str] = None
    description_md: str = ""
    attributes: List[AttributeGroup] = field(default_factory=list)
    media_refs: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> Model:
        return Model(
            sku=str(d.get("sku", "") or ""),
            name=str(d.get("name", "") or ""),
            price=(float(d["price"]) if "price" in d and d["price"] not in (None, "") else None),
            currency=(str(d.get("currency")) if d.get("currency") is not None else None),
            unit=(str(d.get("unit")) if d.get("unit") is not None else None),
            image=(str(d.get("image")) if d.get("image") is not None else None),
            description_md=str(d.get("description_md", "") or ""),
            attributes=[AttributeGroup.from_dict(g) for g in (d.get("attributes") or [])],
            media_refs=[str(x) for x in (d.get("media_refs") or [])],
        )


# ==========
# Series / Section / Accessory
# ==========

@dataclass
class Accessory:
    sku: str
    name: str
    image: Optional[str] = None

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> Accessory:
        return Accessory(
            sku=str(d.get("sku", "") or ""),
            name=str(d.get("name", "") or ""),
            image=(str(d.get("image")) if d.get("image") is not None else None),
        )


@dataclass
class Series:
    code: str
    name: str
    tags: List[str] = field(default_factory=list)
    summary_md: str = ""
    construction_md: str = ""
    features: str = ""
    hero: Hero = field(default_factory=Hero)
    tables: List[Table] = field(default_factory=list)
    media: List[MediaItem] = field(default_factory=list)
    models: List[Model] = field(default_factory=list)
    accessories: List[Accessory] = field(default_factory=list)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> Series:
        return Series(
            code=str(d.get("code", "") or ""),
            name=str(d.get("name", "") or ""),
            tags=[str(t) for t in (d.get("tags") or [])],
            summary_md=str(d.get("summary_md", "") or ""),
            construction_md=str(d.get("construction_md", "") or ""),
            features=str(d.get("features", "") or ""),
            hero=Hero.from_dict(d.get("hero")),
            tables=[Table.from_dict(t) for t in (d.get("tables") or [])],
            media=[MediaItem.from_dict(m) for m in (d.get("media") or [])],
            models=[Model.from_dict(m) for m in (d.get("models") or [])],
            accessories=[Accessory.from_dict(a) for a in (d.get("accessories") or [])],
        )


@dataclass
class Section:
    code: str
    title: str
    intro_md: str = ""
    series: List[Series] = field(default_factory=list)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> Section:
        return Section(
            code=str(d.get("code", "") or ""),
            title=str(d.get("title", "") or ""),
            intro_md=str(d.get("intro_md", "") or ""),
            series=[Series.from_dict(s) for s in (d.get("series") or [])],
        )


# ==========
# Catalog (root)
# ==========

@dataclass
class Catalog:
    settings: Settings
    sections: List[Section]

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> Catalog:
        return Catalog(
            settings=Settings.from_dict(d.get("settings")),
            sections=[Section.from_dict(s) for s in (d.get("sections") or [])],
        )


# ==========
# Rendering blocks (для TOC/якорей/пагинации)
# ==========

@dataclass
class Block:
    """
    Унифицированный блок для пайплайна рендеринга/TOC.
    """
    block_id: str
    type: str                      # "section_heading", "spec_table", "gallery", ...
    title: Optional[str] = None
    subtitle: Optional[str] = None
    category_id: Optional[str] = None
    sku_list: Optional[str] = None
    layout: Optional[str] = None
    columns: Optional[int] = None
    params: Dict[str, Any] = field(default_factory=dict)
    page_break_before: bool = False
    show_in_toc: bool = False
    order: int = 0
    parent_id: Optional[str] = None   # КЛЮЧЕВОЕ для иерархии TOC


@dataclass
class ModelBundle:
    """
    Структура, с которой работают стадии (stages/*):
      - settings/sections (исходные данные)
      - blocks (линейная последовательность блоков для рендеринга)
      - block_index (быстрый поиск по id)
    """
    settings: Settings
    sections: List[Section]
    blocks: List[Block] = field(default_factory=list)
    block_index: Dict[str, Block] = field(default_factory=dict)

    def rebuild_index(self) -> None:
        self.block_index = {b.block_id: b for b in self.blocks}


# ==========
# Вспомогательные построители блоков
# ==========

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


def build_toc_blocks(cat: Catalog) -> List[Block]:
    """
    Формирует только заголовки для TOC: Section (L1) → Series (L2).
    Анкоры в шаблонах должны использовать id="sec-{{ block_id }}".
    """
    blocks: List[Block] = []
    order = 0

    for sec in cat.sections:
        # L1 — тип оборудования (Section)
        sec_block_id = _new_block_id("sec", sec.code or sec.title)
        blocks.append(Block(
            block_id=sec_block_id,
            type="section_heading",
            title=sec.title or sec.code,
            params={"toc_level": 1},
            show_in_toc=True,
            order=order,
        ))
        order += 10

        # L2 — серии внутри типа
        for ser in sec.series:
            ser_block_id = _new_block_id("ser", ser.code or ser.name)
            blocks.append(Block(
                block_id=ser_block_id,
                type="section_heading",
                title=ser.name or ser.code,
                params={"toc_level": 2},
                show_in_toc=True,
                order=order,
                parent_id=sec_block_id,  # привязка к типу (L1)
            ))
            order += 10

            # Пример: можно добавить сводную «таблицу серии» (если нужна в TOC — включайте явно)
            # blocks.append(Block(
            #     block_id=_new_block_id("tbl", ser.code),
            #     type="spec_table",
            #     title=f"Тех. характеристики — {ser.name}",
            #     params={"toc_level": 2},
            #     show_in_toc=False,           # по умолчанию не включаем в TOC
            #     order=order,
            #     parent_id=ser_block_id,      # принадлежит серии
            # ))
            # order += 10

    return blocks


def build_model_bundle(cat: Catalog) -> ModelBundle:
    """
    Создаёт ModelBundle с blocks, пригодными для TOC «тип → серия».
    Контентные блоки (карточки моделей, таблицы, галереи) вы можете
    добавлять своей стадией — достаточно выставлять parent_id по вложенности.
    """
    blocks = build_toc_blocks(cat)
    mb = ModelBundle(settings=cat.settings, sections=cat.sections, blocks=blocks)
    mb.rebuild_index()
    return mb


# ==========
# Утилита загрузки из dict
# ==========

def load_catalog(data: Dict[str, Any]) -> ModelBundle:
    """
    Главная точка входа: из JSON-dict собираем Catalog и ModelBundle.
    """
    cat = Catalog.from_dict(data)
    return build_model_bundle(cat)
