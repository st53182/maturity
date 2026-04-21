"""AI report analyzer for business owners.

Accepts an arbitrary report (HTML / text / image / CSV) and returns a structured
list of insights that may deserve attention: data discrepancies, suspicious
values, trend breaks, outliers, etc. Works for IT and finance reports.
"""
from __future__ import annotations

import base64
import json
import os
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from openai import OpenAI

bp_report_insights = Blueprint("report_insights", __name__, url_prefix="/api/report-insights")

MAX_TEXT_CHARS = 30_000
MAX_FILE_BYTES = 6 * 1024 * 1024
ALLOWED_IMAGE_MIMES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


def _openai_client() -> Optional[OpenAI]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def _locale_label(locale: str) -> str:
    loc = (locale or "ru").strip().lower()
    return "English" if loc.startswith("en") else "Russian"


def _html_to_text(raw_html: str) -> Dict[str, Any]:
    """Extracts readable text from HTML plus a bag of summary tables.

    Keeps table structure hints (first 80 rows per table) so that the model
    can reason about data discrepancies rather than free-form prose.
    """
    soup = BeautifulSoup(raw_html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = (soup.title.string.strip() if soup.title and soup.title.string else "") or ""

    tables_text: List[str] = []
    for idx, table in enumerate(soup.find_all("table")[:10], 1):
        rows: List[str] = []
        for row in table.find_all("tr")[:80]:
            cells = [re.sub(r"\s+", " ", c.get_text(" ", strip=True))[:160]
                     for c in row.find_all(["th", "td"])]
            if cells:
                rows.append(" | ".join(cells))
        if rows:
            tables_text.append(f"[Table {idx}]\n" + "\n".join(rows))

    # narrative body
    body = soup.body if soup.body else soup
    text = body.get_text("\n", strip=True)
    text = re.sub(r"\n{2,}", "\n\n", text)

    return {
        "title": title[:200],
        "body": text[:MAX_TEXT_CHARS],
        "tables": tables_text,
    }


def _looks_like_pdf(raw: bytes) -> bool:
    return raw[:4] == b"%PDF"


def _pdf_to_text(raw: bytes) -> str:
    """Best-effort PDF -> text.  pdfplumber / pypdf are optional deps, so we
    fail gracefully if nothing suitable is installed."""
    try:
        import pdfplumber  # type: ignore
        import io

        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            chunks = []
            for page in pdf.pages[:40]:
                chunks.append(page.extract_text() or "")
        return "\n".join(chunks)[:MAX_TEXT_CHARS]
    except Exception:
        pass

    try:
        from pypdf import PdfReader  # type: ignore
        import io

        reader = PdfReader(io.BytesIO(raw))
        chunks = []
        for page in reader.pages[:40]:
            chunks.append(page.extract_text() or "")
        return "\n".join(chunks)[:MAX_TEXT_CHARS]
    except Exception:
        return ""


def _system_prompt(locale: str) -> str:
    lang = _locale_label(locale)
    return (
        "You are a senior analyst reviewing a business report for a C-level owner. "
        "Your job is to point out everything that might deserve attention: "
        "data discrepancies, sudden trend changes, suspicious outliers, "
        "mismatched totals, anomalies in finance / IT / delivery metrics, "
        "unusually slow or fast moving items, and any risks implied by the data. "
        f"Write all human-readable fields in {lang}. "
        "Respond with a single JSON object only, no markdown, no commentary."
    )


def _user_prompt(content_blocks: List[str], meta: Dict[str, Any]) -> str:
    joined = "\n\n".join(content_blocks)[:MAX_TEXT_CHARS]
    meta_json = json.dumps(meta, ensure_ascii=False)[:2000]
    return (
        f"Report meta: {meta_json}\n\n"
        f"Report content (may be truncated):\n\n{joined}\n\n"
        'Return JSON of the form: {\n'
        '  "summary": "2-4 sentences: what this report is about and the overall state",\n'
        '  "health": "green|yellow|red",\n'
        '  "kpis": [{"label": "", "value": "", "comment": ""}],\n'
        '  "insights": [{\n'
        '      "title": "short headline",\n'
        '      "severity": "info|watch|warning|critical",\n'
        '      "category": "data_quality|trend|outlier|finance|performance|risk|opportunity|other",\n'
        '      "evidence": "the numbers or phrases from the report this is based on",\n'
        '      "why_it_matters": "why a business owner should care",\n'
        '      "suggested_action": "1-2 concrete next steps"\n'
        '  }],\n'
        '  "questions_to_ask": ["open questions to raise with the team"]\n'
        '}\n'
        "Give 4–10 insights total. Be specific, quote values when possible, "
        "and do NOT invent data that is not in the report."
    )


def _parse_with_text(text_blocks: List[str], meta: Dict[str, Any], locale: str) -> Dict[str, Any]:
    client = _openai_client()
    if not client:
        raise RuntimeError("OpenAI API is not configured")
    resp = client.chat.completions.create(
        model=os.getenv("REPORT_INSIGHTS_MODEL", "gpt-4.1"),
        messages=[
            {"role": "system", "content": _system_prompt(locale)},
            {"role": "user", "content": _user_prompt(text_blocks, meta)},
        ],
        temperature=0.25,
        max_tokens=2800,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content or "{}"
    return json.loads(raw)


def _parse_with_image(raw: bytes, mime: str, meta: Dict[str, Any], locale: str) -> Dict[str, Any]:
    client = _openai_client()
    if not client:
        raise RuntimeError("OpenAI API is not configured")
    mime = mime if mime in ALLOWED_IMAGE_MIMES else "image/png"
    b64 = base64.b64encode(raw).decode("ascii")
    user_text = _user_prompt(
        ["(image report attached — read all numbers / labels you can see)"],
        meta,
    )
    resp = client.chat.completions.create(
        model=os.getenv("REPORT_INSIGHTS_VISION_MODEL", "gpt-4.1"),
        messages=[
            {"role": "system", "content": _system_prompt(locale)},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            },
        ],
        temperature=0.25,
        max_tokens=2800,
        response_format={"type": "json_object"},
    )
    raw_txt = resp.choices[0].message.content or "{}"
    return json.loads(raw_txt)


def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {"summary": "", "health": "yellow", "kpis": [], "insights": [], "questions_to_ask": []}

    health = str(data.get("health") or "yellow").lower()
    if health not in {"green", "yellow", "red"}:
        health = "yellow"

    def _clean_list(raw_list, keys_required):
        out = []
        for item in (raw_list or []):
            if not isinstance(item, dict):
                continue
            out.append({k: (str(item.get(k) or "")[:800]) for k in keys_required})
        return out

    insights_keys = [
        "title", "severity", "category", "evidence",
        "why_it_matters", "suggested_action",
    ]
    kpi_keys = ["label", "value", "comment"]

    return {
        "summary": str(data.get("summary") or "")[:1200],
        "health": health,
        "kpis": _clean_list(data.get("kpis"), kpi_keys),
        "insights": _clean_list(data.get("insights"), insights_keys),
        "questions_to_ask": [
            str(q)[:400]
            for q in (data.get("questions_to_ask") or [])
            if isinstance(q, (str, int, float))
        ][:10],
    }


@bp_report_insights.route("/analyze", methods=["POST"])
@jwt_required()
def analyze():
    """Primary endpoint.

    Two modes, selected by Content-Type:
      * multipart/form-data — file upload: `file` (html / pdf / image / txt / csv)
        with optional `locale`, `notes` form fields.
      * application/json — `{ text, locale, notes }`.
    """
    locale = (request.args.get("locale") or request.form.get("locale") or "").strip() or "ru"
    notes_raw = (request.args.get("notes") or request.form.get("notes") or "").strip()[:1500]

    meta: Dict[str, Any] = {"user_notes": notes_raw, "locale": locale}

    try:
        if request.content_type and "multipart/form-data" in request.content_type:
            f = request.files.get("file")
            if not f or not f.filename:
                return jsonify({"error": "file is required"}), 400
            raw = f.read()
            if len(raw) > MAX_FILE_BYTES:
                return jsonify({"error": "file too large (max 6 MB)"}), 400
            mime = (f.mimetype or "").lower()
            name = (f.filename or "").lower()
            meta.update({"filename": f.filename[:180], "mime": mime})

            if mime in ALLOWED_IMAGE_MIMES or name.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                data = _parse_with_image(raw, mime, meta, locale)
                return jsonify(_normalize(data))

            if mime == "application/pdf" or name.endswith(".pdf") or _looks_like_pdf(raw):
                text = _pdf_to_text(raw)
                if not text.strip():
                    return jsonify({"error": "Could not read this PDF on the server"}), 422
                data = _parse_with_text([text], meta, locale)
                return jsonify(_normalize(data))

            try:
                decoded = raw.decode("utf-8", errors="replace")
            except Exception:
                decoded = ""
            if mime in ("text/html", "application/xhtml+xml") or name.endswith((".html", ".htm")):
                parsed = _html_to_text(decoded)
                meta.update({"title": parsed["title"]})
                blocks = [parsed["body"]]
                if parsed["tables"]:
                    blocks.append("\n\n".join(parsed["tables"]))
                data = _parse_with_text(blocks, meta, locale)
                return jsonify(_normalize(data))

            # plain text / csv / json fall-through
            if decoded.strip():
                data = _parse_with_text([decoded[:MAX_TEXT_CHARS]], meta, locale)
                return jsonify(_normalize(data))

            return jsonify({"error": "unsupported file format"}), 415

        payload = request.get_json(silent=True) or {}
        text = str(payload.get("text") or "").strip()
        if not text:
            return jsonify({"error": "provide text or upload a file"}), 400
        locale = (str(payload.get("locale") or "ru")).strip()[:12] or "ru"
        notes_raw = str(payload.get("notes") or "")[:1500]
        meta.update({"locale": locale, "user_notes": notes_raw})

        if text.lstrip().lower().startswith(("<!doctype html", "<html")):
            parsed = _html_to_text(text)
            meta.update({"title": parsed["title"]})
            blocks = [parsed["body"]]
            if parsed["tables"]:
                blocks.append("\n\n".join(parsed["tables"]))
            data = _parse_with_text(blocks, meta, locale)
        else:
            data = _parse_with_text([text[:MAX_TEXT_CHARS]], meta, locale)
        return jsonify(_normalize(data))

    except json.JSONDecodeError:
        return jsonify({"error": "AI returned invalid JSON"}), 502
    except RuntimeError as e:
        return jsonify({"error": str(e)[:400]}), 503
    except Exception as e:  # pragma: no cover - safety net
        print(f"report_insights.analyze: {e}")
        return jsonify({"error": "analysis failed"}), 500
