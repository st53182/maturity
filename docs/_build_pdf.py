"""Convert the GrowBoard API guide from Markdown to PDF (Cyrillic-friendly).

Uses fpdf2 (pure Python) with TTF fonts from C:\\Windows\\Fonts, so Cyrillic
renders correctly without any system dependencies.

Usage:
    python docs/_build_pdf.py

Dependencies:
    pip install --user markdown fpdf2
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import markdown
from bs4 import BeautifulSoup
from fpdf import FPDF
from fpdf.fonts import FontFace
from fpdf.enums import TextEmphasis

DOCS = Path(__file__).resolve().parent
SRC = DOCS / "api_postman_guide.md"
DST = DOCS / "api_postman_guide.pdf"

WIN_FONTS = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
FONT_REGULAR = WIN_FONTS / "arial.ttf"
FONT_BOLD = WIN_FONTS / "arialbd.ttf"
FONT_ITALIC = WIN_FONTS / "ariali.ttf"
FONT_BOLDITALIC = WIN_FONTS / "arialbi.ttf"
FONT_MONO = WIN_FONTS / "consola.ttf"
FONT_MONO_BOLD = WIN_FONTS / "consolab.ttf"

for f in (FONT_REGULAR, FONT_BOLD, FONT_MONO):
    if not f.exists():
        raise SystemExit(f"Required font missing: {f}")


def _sanitize_for_fpdf(html: str) -> str:
    """fpdf2's write_html can't handle nested inline tags inside <td>/<th>
    or complex block structures inside list items. Flatten those cases."""
    soup = BeautifulSoup(html, "html.parser")

    # Unwrap inline tags inside table cells: keep text, drop the tag.
    for cell in soup.find_all(["td", "th"]):
        for inline in cell.find_all(["code", "em", "strong", "i", "b", "a", "span"]):
            inline.unwrap()

    # Same for <li> — fpdf2 doesn't like <code>/<a> nested there either.
    for li in soup.find_all("li"):
        for inline in li.find_all(["code", "em", "strong", "i", "b", "a", "span"]):
            inline.unwrap()

    # Replace <hr/> with a simple blank line paragraph (fpdf2 renders it poorly).
    for hr in soup.find_all("hr"):
        p = soup.new_tag("p")
        p.string = "\u2500" * 60
        hr.replace_with(p)

    return str(soup)


def _register_fonts(pdf: FPDF) -> None:
    pdf.add_font("UI", style="", fname=str(FONT_REGULAR))
    pdf.add_font("UI", style="B", fname=str(FONT_BOLD))
    if FONT_ITALIC.exists():
        pdf.add_font("UI", style="I", fname=str(FONT_ITALIC))
    if FONT_BOLDITALIC.exists():
        pdf.add_font("UI", style="BI", fname=str(FONT_BOLDITALIC))
    pdf.add_font("UIMono", style="", fname=str(FONT_MONO))
    if FONT_MONO_BOLD.exists():
        pdf.add_font("UIMono", style="B", fname=str(FONT_MONO_BOLD))


def build() -> int:
    if not SRC.exists():
        print(f"source not found: {SRC}", file=sys.stderr)
        return 2

    md_text = SRC.read_text(encoding="utf-8")
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html5",
    )
    html_body = _sanitize_for_fpdf(html_body)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=16, top=16, right=16)
    pdf.set_auto_page_break(auto=True, margin=16)
    _register_fonts(pdf)

    pdf.add_page()
    pdf.set_font("UI", size=10)
    pdf.set_text_color(10, 20, 45)

    def ff(size: int, bold: bool = False, color: tuple[int, int, int] = (10, 20, 45), mono: bool = False):
        family = "UIMono" if mono else "UI"
        emph = TextEmphasis.B if bold else TextEmphasis.NONE
        return FontFace(family=family, emphasis=emph, size_pt=size, color=color)

    tag_styles = {
        "h1": ff(20, True, (24, 70, 200)),
        "h2": ff(15, True, (24, 70, 200)),
        "h3": ff(12, True, (32, 50, 95)),
        "h4": ff(11, True, (32, 50, 95)),
        "h5": ff(10, True, (32, 50, 95)),
        "h6": ff(10, True, (32, 50, 95)),
        "code": ff(9, False, (19, 48, 109), mono=True),
        "pre": ff(9, False, (10, 20, 45), mono=True),
        "a": ff(10, False, (29, 78, 216)),
        "blockquote": ff(10, False, (32, 50, 95)),
    }

    pdf.write_html(html_body, tag_styles=tag_styles, font_family="UI")

    tmp = DST.with_suffix(".tmp.pdf")
    pdf.output(str(tmp))

    try:
        if DST.exists():
            DST.unlink()
        tmp.rename(DST)
        target = DST
    except PermissionError:
        print(f"NOTE: {DST} is locked (probably open in a viewer), wrote {tmp} instead.", file=sys.stderr)
        target = tmp
    print(f"written: {target} ({target.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
