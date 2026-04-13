# Локализация опроса зрелости по ссылке (EN): строки опроса и глоссарий.
import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
_SURVEY_EN_PATH = os.path.join(_DIR, "maturity_survey_en.json")
_GLOSSARY_EN_PATH = os.path.join(_DIR, "maturity_glossary_en.json")

_SURVEY_EN_ROWS = None
_GLOSSARY_EN_ROWS = None

BUSINESS_METRICS_DISCLAIMER_EN = (
    "Business metrics impact is illustrated using banks as an example (including Citibank, Deutsche Bank). "
    "Metrics include: NOI, cost reduction, Retention / Churn, DAU/MAU, LTV, MRR/ARR, "
    "CPA, Cost per Approved Client, application conversion, card activation, revenue "
    "(Interchange, Interest, Fee, ARPU), delinquency and NPL. The link between a practice and a metric "
    "is often transitive rather than direct."
)

ROLE_LABEL_EN = {
    "Владелец продукта": "Product Owner",
    "Менеджер продукта/dPO": "Product Manager / dPO",
    "Участники команды": "Team members",
    "ИТ-лидер Стрима": "Stream IT leader",
    "Скрам-мастер": "Scrum Master",
    "Технический лидер": "Technical lead",
    "Владелец Стрима": "Stream Owner",
    "Заказчик": "Customer / sponsor",
}


def _load_json_list(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else None
    except (json.JSONDecodeError, OSError):
        return None


def load_survey_en_rows():
    global _SURVEY_EN_ROWS
    if _SURVEY_EN_ROWS is None:
        _SURVEY_EN_ROWS = _load_json_list(_SURVEY_EN_PATH) or []
    return _SURVEY_EN_ROWS


def load_glossary_en_rows():
    global _GLOSSARY_EN_ROWS
    if _GLOSSARY_EN_ROWS is None:
        _GLOSSARY_EN_ROWS = _load_json_list(_GLOSSARY_EN_PATH) or []
    return _GLOSSARY_EN_ROWS


def resolve_survey_lang(request, session=None):
    """Язык текста вопросов: ?lang= → сохранённый в сессии survey_locale → Accept-Language → ru."""
    q = (request.args.get("lang") or "").strip().lower()
    if q in ("en", "ru"):
        return q
    if session is not None:
        sl = getattr(session, "survey_locale", None)
        if isinstance(sl, str) and sl.lower() in ("en", "ru"):
            return sl.lower()
    accept = (request.headers.get("Accept-Language") or "").lower()
    if accept.startswith("en") or ",en" in accept:
        return "en"
    return "ru"


def localize_question_dict(index, qdict, lang):
    if lang != "en":
        return qdict
    rows = load_survey_en_rows()
    if not rows or index >= len(rows):
        return qdict
    ov = rows[index] or {}
    out = dict(qdict)
    t = (ov.get("text") or "").strip()
    if t:
        out["text"] = t
    # Keep canonical RU `theme` for grouping with radar/results keys; UI translates via i18n.
    for k in ("why_important", "category", "metrics_impact", "negative_for_business", "business_metrics"):
        v = (ov.get(k) or "").strip()
        if v:
            out[k] = v
    return out


def localize_related_roles(roles, lang):
    if lang != "en" or not roles:
        return roles
    return [ROLE_LABEL_EN.get(r, r) for r in roles]


def localized_business_metrics_disclaimer(lang):
    from maturity_questions import BUSINESS_METRICS_DISCLAIMER

    if lang == "en":
        return BUSINESS_METRICS_DISCLAIMER_EN
    return BUSINESS_METRICS_DISCLAIMER


def localized_business_metrics_glossary(base_glossary, lang):
    if lang != "en":
        return base_glossary
    enriched = load_glossary_en_rows()
    if len(enriched) != len(base_glossary):
        return base_glossary
    out = []
    for i, g in enumerate(base_glossary):
        row = enriched[i] if i < len(enriched) else {}
        name = (row.get("name_en") or "").strip() or g.get("name", "")
        desc = (row.get("description_en") or "").strip() or g.get("description", "")
        out.append({**g, "name": name, "description": desc})
    return out
