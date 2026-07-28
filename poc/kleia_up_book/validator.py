"""
KLEIA-UP Book — Validation Module
EPUB structure, PDF metrics, content integrity, quality scoring
"""

import os, re, zipfile, json
from pathlib import Path
from xml.etree import ElementTree as ET


def validate_epub(epub_path: str) -> dict:
    """Validate EPUB structure and content integrity."""
    results = {"valid": True, "checks": [], "score": 0, "details": {}}
    score = 0
    max_score = 11

    try:
        with zipfile.ZipFile(epub_path, 'r') as zf:
            names = zf.namelist()

            # 1. mimetype
            if "mimetype" in names:
                mt = zf.read("mimetype").decode("utf-8").strip()
                if mt == "application/epub+zip":
                    results["checks"].append({"check": "mimetype", "pass": True})
                    score += 1
                else:
                    results["checks"].append({"check": "mimetype", "pass": False, "detail": f"Bad mimetype: {mt}"})
            else:
                results["checks"].append({"check": "mimetype", "pass": False, "detail": "Missing mimetype"})

            # 2. META-INF/container.xml
            if "META-INF/container.xml" in names:
                results["checks"].append({"check": "container.xml", "pass": True})
                score += 1
            else:
                results["checks"].append({"check": "container.xml", "pass": False, "detail": "Missing container.xml"})

            # 3. OPF presence
            opf_files = [n for n in names if n.endswith(".opf")]
            if opf_files:
                results["details"]["opf"] = opf_files[0]
                results["checks"].append({"check": "OPF", "pass": True})
                score += 1

                # Parse OPF
                try:
                    opf = ET.parse(zf.open(opf_files[0]))
                    ns = {"opf": "http://www.idpf.org/2007/opf",
                          "dc": "http://purl.org/dc/elements/1.1/"}
                    # Title
                    titles = opf.findall(".//dc:title", ns)
                    results["details"]["title"] = titles[0].text if titles else None
                    # Author
                    authors = opf.findall(".//dc:creator", ns)
                    results["details"]["author"] = authors[0].text if authors else None
                    # Language
                    langs = opf.findall(".//dc:language", ns)
                    results["details"]["language"] = langs[0].text if langs else None
                    results["checks"].append({"check": "OPF metadata", "pass": True})
                    score += 1
                except Exception as e:
                    results["checks"].append({"check": "OPF parse", "pass": False, "detail": str(e)})
            else:
                results["checks"].append({"check": "OPF", "pass": False, "detail": "Missing OPF"})

            # 4. Nav / TOC
            has_nav = any("nav" in n.lower() for n in names)
            results["checks"].append({"check": "Navigation", "pass": has_nav})
            if has_nav: score += 1

            # 5. Content files (at least one XHTML)
            xhtml = [n for n in names if n.endswith((".xhtml", ".html", ".htm"))]
            results["details"]["content_files"] = len(xhtml)
            results["checks"].append({"check": "Content files", "pass": len(xhtml) > 0})
            if len(xhtml) > 0: score += 1

            # 6. CSS
            css = [n for n in names if n.endswith(".css")]
            results["details"]["css_files"] = len(css)
            results["checks"].append({"check": "CSS styles", "pass": len(css) > 0})
            if len(css) > 0: score += 1

            # 7. No broken files (all readable)
            broken = 0
            for n in names:
                try:
                    zf.read(n)
                except Exception:
                    broken += 1
            results["checks"].append({"check": "All files readable", "pass": broken == 0})
            if broken == 0: score += 1
            if broken:
                results["details"]["broken_files"] = broken

            # 8. EPUB version
            if opf_files:
                opf_content = zf.read(opf_files[0]).decode("utf-8", errors="replace")
                is_v3 = 'version="3.0"' in opf_content
                results["details"]["epub_version"] = "3.0" if is_v3 else "2.0"
                results["checks"].append({"check": "EPUB 3", "pass": is_v3})
                if is_v3: score += 1

        # 9. File size reasonability
        sz_kb = os.path.getsize(epub_path) / 1024
        results["details"]["size_kb"] = round(sz_kb, 1)
        results["checks"].append({"check": "File size > 1KB", "pass": sz_kb > 1})
        if sz_kb > 1: score += 1

    except zipfile.BadZipFile:
        results["valid"] = False
        results["checks"].append({"check": "ZIP format", "pass": False, "detail": "Not a valid ZIP file"})

    # Final score
    results["score"] = round(score / max_score * 100)
    results["valid"] = results["score"] >= 70
    return results


def validate_pdf(pdf_path: str) -> dict:
    """Validate PDF print-ready properties."""
    results = {"checks": [], "score": 0, "details": {}}
    score = 0
    max_score = 5

    sz = os.path.getsize(pdf_path)
    sz_kb = sz / 1024
    results["details"]["size_kb"] = round(sz_kb, 1)
    results["checks"].append({"check": "File size > 10KB", "pass": sz_kb > 10})
    if sz_kb > 10: score += 1

    # Check file header for PDF magic bytes
    with open(pdf_path, "rb") as f:
        header = f.read(5)
        is_pdf = header == b"%PDF-"
    results["checks"].append({"check": "Valid PDF header", "pass": is_pdf})
    if is_pdf: score += 1

    # Multi-page check (try to count pages via simple heuristic)
    with open(pdf_path, "rb") as f:
        content = f.read()
    page_count = content.count(b"/Type /Page") - content.count(b"/Type /Pages")
    results["details"]["estimated_pages"] = max(page_count, 1)
    results["checks"].append({"check": "Multi-page", "pass": page_count > 1})
    if page_count > 1: score += 1

    # Contains text (not empty/scanned only)
    has_text = len(re.findall(rb'\(([^)]*)\)', content)) > 10
    results["checks"].append({"check": "Contains text", "pass": has_text})
    if has_text: score += 1

    results["score"] = round(score / max_score * 100)
    return results


def quality_score(epub_result: dict, pdf_result: dict = None) -> dict:
    """Aggregate quality score from all validations."""
    epub = epub_result.get("score", 0)
    pdf = pdf_result.get("score", 0) if pdf_result else 0

    # Weighted: EPUB more important than PDF
    total = epub * 0.6 + pdf * 0.4 if pdf_result else epub

    grade = "A" if total >= 90 else "B" if total >= 75 else "C" if total >= 50 else "D"

    return {
        "score": round(total),
        "grade": grade,
        "epub_score": epub,
        "pdf_score": pdf,
        "epub_checks": epub_result.get("checks", []),
        "pdf_checks": pdf_result.get("checks", []) if pdf_result else [],
        "details": {
            "epub": epub_result.get("details", {}),
            "pdf": pdf_result.get("details", {}) if pdf_result else {},
        }
    }


def validate_book(output_dir: str, epub_name: str, pdf_name: str = None) -> dict:
    """Run all validations on a book's output files."""
    epub_path = os.path.join(output_dir, epub_name)
    if not os.path.exists(epub_path):
        return {"error": f"EPUB not found: {epub_path}"}

    # EPUB validation
    epub_result = validate_epub(epub_path)

    # PDF validation (optional)
    pdf_result = None
    if pdf_name:
        pdf_path = os.path.join(output_dir, pdf_name)
        if os.path.exists(pdf_path):
            pdf_result = validate_pdf(pdf_path)

    # Aggregate
    return quality_score(epub_result, pdf_result)
