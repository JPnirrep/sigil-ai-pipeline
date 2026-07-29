/* KLEIA-UP Book Editor — Type definitions */

export interface Chapter {
  id: string;
  title: string;
  content_html: string;
}

export interface Book {
  id: string;
  title: string;
  subtitle: string;
  author: string;
  front_matter_html: string;
  chapters: Chapter[];
  trim_width: number;
  trim_height: number;
  margin_top: number;
  margin_bottom: number;
  margin_inner: number;
  margin_outer: number;
  bleed: number;
}

export interface StyleOverrides {
  body_font: string;
  body_size: string;
  body_line_height: string;
  body_alignment: string;
  body_margin_bottom: string;
  body_color: string;
  h1_font: string;
  h1_size: string;
  h1_weight: string;
  h1_align: string;
  h1_color: string;
  h1_margin_top: string;
  h1_margin_bottom: string;
  h2_font: string;
  h2_size: string;
  h2_weight: string;
  h2_align: string;
  h2_color: string;
  h2_margin_top: string;
  h2_margin_bottom: string;
  h3_font: string;
  h3_size: string;
  h3_weight: string;
  h3_align: string;
  h3_color: string;
  image_max_width: string;
  image_align: string;
}

export interface BookMetadata {
  word_count: number;
  chapter_count: number;
  parsed_at: string;
  source_file: string;
  genre_detected: string;
}

export interface BookState {
  book: Book | null;
  style: StyleOverrides;
  metadata: BookMetadata | null;
}

export interface SessionInfo {
  id: string;
  source: string;
  has_book: boolean;
  metadata: BookMetadata | null;
}

export interface TemplateInfo {
  name: string;
  filename: string;
  size: number;
  size_str: string;
}
