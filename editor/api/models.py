"""
KLEIA-UP Book Editor — Pydantic models
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class ChapterModel(BaseModel):
    id: str
    title: str
    content_html: str = ""  # Rich HTML from TipTap


class BookModel(BaseModel):
    id: str
    title: str = ""
    subtitle: str = ""
    author: str = ""
    front_matter_html: str = ""  # Title page + front matter as HTML
    chapters: List[ChapterModel] = Field(default_factory=list)
    trim_width: float = 6.0
    trim_height: float = 9.0
    margin_top: float = 0.6
    margin_bottom: float = 0.7
    margin_inner: float = 0.8
    margin_outer: float = 0.5
    bleed: float = 0.125


class StyleOverrides(BaseModel):
    body_font: str = "Georgia, 'Times New Roman', serif"
    body_size: str = "11pt"
    body_line_height: str = "1.5"
    body_alignment: str = "justify"
    body_margin_bottom: str = "0.3em"
    body_color: str = "#333333"

    h1_font: str = "Georgia, 'Times New Roman', serif"
    h1_size: str = "24pt"
    h1_weight: str = "bold"
    h1_align: str = "left"
    h1_color: str = "#1a1a2e"
    h1_margin_top: str = "2em"
    h1_margin_bottom: str = "0.5em"

    h2_font: str = "Georgia, 'Times New Roman', serif"
    h2_size: str = "18pt"
    h2_weight: str = "bold"
    h2_align: str = "left"
    h2_color: str = "#333333"
    h2_margin_top: str = "1.5em"
    h2_margin_bottom: str = "0.3em"

    h3_font: str = "Georgia, 'Times New Roman', serif"
    h3_size: str = "14pt"
    h3_weight: str = "bold"
    h3_align: str = "left"
    h3_color: str = "#555555"

    image_max_width: str = "100%"
    image_align: str = "center"


class BookMetadata(BaseModel):
    word_count: int = 0
    chapter_count: int = 0
    parsed_at: str = ""
    source_file: str = ""
    genre_detected: str = "default"
