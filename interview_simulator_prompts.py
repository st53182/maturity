# Prompt templates for AI Interview Simulator (MVP).
# Keep role / level / job description explicit so the model anchors on JD requirements.

import json
from typing import Optional

def interview_language_block(locale: str) -> str:
    """Natural language for questions, closings, evaluations, and report must match UI locale."""
    lc = (locale or "en").strip().lower()
    if lc.startswith("ru"):
        return """Language (mandatory):
- The candidate uses the Russian UI. The entire interview must be in natural Russian.
- Every candidate-facing string in your JSON ("question", closings, "summary", "strengths", "gaps", "follow_up_hint", report text fields, etc.) MUST be in Russian.
- JSON keys must remain exactly as in the schema (English).
- Technical terms: use English where it is standard in Russian IT speech (API, Docker, CI/CD); otherwise prefer Russian."""
    return """Language:
- Conduct the interview in clear English; all candidate-facing strings in English."""


SYSTEM_BASE = """You are an expert technical interviewer. You conduct structured interviews fairly.
Rules:
- Ask ONE clear question at a time (no bullet lists of multiple unrelated questions).
- Do not reveal scores to the candidate during the interview.
- If a job description (JD) is provided, you MUST tie questions and follow-ups to its requirements, stack, and responsibilities.
- Adapt difficulty to the stated seniority level.
- If an answer is shallow, ask ONE concise follow-up that probes depth on the same topic — use NEW wording and a more specific angle; never repeat the previous question verbatim or as a light paraphrase.
- Never ask two main questions in a row that target the same subtopic (e.g. two generic "tell me about testing" prompts). Vary focus across the interview.
- Output ONLY valid JSON matching the schema requested in the user message (no markdown fences)."""

# Rotating themes so consecutive questions explore different angles (reduces repetitive LLM outputs).
_QUESTION_THEMES = [
    "A concrete past situation (STAR-style): problem, your role, outcome, metrics.",
    "Technical trade-offs: two valid options and how you chose in practice.",
    "Production / incident / debugging: how you found root cause and prevented recurrence.",
    "Quality & testing: strategy, automation, what you would not compromise on.",
    "Collaboration: code review, disagreement with a peer or PM, how you resolved it.",
    "Scale, performance, or reliability: bottleneck, monitoring, or capacity.",
    "Security, privacy, or data handling relevant to the role.",
    "Delivery & prioritization under constraints (time, scope, tech debt).",
    "Deep dive into one specific tool, pattern, or stack item from the JD (if JD exists); else core skill for the role.",
    "Learning & mentorship: how you stay current or helped others grow.",
]


def _prior_assistant_questions(transcript_json: str, limit: int = 14) -> list[str]:
    try:
        arr = json.loads(transcript_json)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(arr, list):
        return []
    out: list[str] = []
    for m in arr:
        if not isinstance(m, dict):
            continue
        if m.get("role") != "assistant":
            continue
        c = (m.get("content") or "").strip()
        if not c:
            continue
        low = c.lower()
        if "completes the interview" in low or ("thank you" in low and "interview" in low):
            continue
        out.append(c)
    return out[-limit:]


def build_question_prompt(
    role: str,
    level: str,
    job_description: Optional[str],
    transcript_json: str,
    question_index: int,
    min_questions: int,
    max_questions: int,
    last_evaluation_json: str | None,
    locale: str = "en",
) -> str:
    jd_block = (
        job_description.strip()
        if job_description and job_description.strip()
        else "(No job description provided — use a standard interview for the role and level.)"
    )
    eval_block = last_evaluation_json or "null"
    prior_qs = _prior_assistant_questions(transcript_json)
    if prior_qs:
        numbered = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(prior_qs))
        anti_repeat = f"""Questions you already asked the candidate (new question must be SUBSTANTIALLY different — different primary skill, scenario, or JD bullet; not a near-duplicate):
{numbered}

Hard rules:
- Do NOT ask the same question again or swap only a few words.
- If the last question was broad, make this one narrow (specific constraint, metric, or artifact), or switch theme entirely.
- If is_follow_up is true, stay on the same TOPIC as the last exchange but change the angle (e.g. numbers, failure mode, decision criteria) — still avoid repeating the previous interviewer sentence structure."""
    else:
        anti_repeat = "(No prior interviewer questions in transcript yet — open with a strong, role-appropriate starter.)"

    theme_idx = question_index % len(_QUESTION_THEMES)
    theme_hint = _QUESTION_THEMES[theme_idx]
    next_theme_idx = (question_index + 1) % len(_QUESTION_THEMES)
    next_theme = _QUESTION_THEMES[next_theme_idx]

    lang = interview_language_block(locale)

    return f"""Generate the next interview step.

{lang}

Context:
- Role: {role}
- Level: {level}
- Progress: question_index is the number of COMPLETED Q&A rounds the client already has (same as questionIndex in the request). The next JSON you return is for the following turn only.
- CRITICAL: If question_index >= {max_questions}, you MUST set "interview_complete": true and set "question" to a short closing line only — do NOT ask another interview question. (The server also enforces this.)
- Target length: between {min_questions} and {max_questions} total interviewer turns (questions + follow-ups count as turns).
- Job description (verbatim; you MUST reference it when present):
---
{jd_block}
---

Suggested focus for THIS turn (primary angle — follow it unless last_evaluation forces a follow-up on the same topic):
- {theme_hint}
- If this is NOT a follow-up, prefer this angle over repeating themes from earlier questions.
- Next turn after this one will lean toward: {next_theme} (plan ahead mentally; do not mention this to the candidate).

{anti_repeat}

Conversation so far (JSON array of {{\\"role\\": \\"assistant\\"|\\"user\\", \\"content\\": \\"...\\"}}):
{transcript_json}

Last answer evaluation (JSON or null):
{eval_block}

Return JSON with this exact shape:
{{
  "question": "string — the next question to ask the candidate (single question)",
  "is_follow_up": true or false,
  "interview_complete": true or false,
  "rationale_internal": "short note why this question (not shown to candidate)"
}}

Set interview_complete to true ONLY if:
- You already asked at least {min_questions} meaningful turns AND further questions add little value, OR
- You reached ~{max_questions} turns (do not exceed {max_questions}).
When interview_complete is true, set question to a short closing line in the interview language (Russian UI: e.g. "Спасибо, на этом интервью завершено."; English: "Thank you, this completes the interview."). """


def build_evaluate_prompt(
    role: str,
    level: str,
    job_description: str | None,
    question: str,
    answer: str,
    locale: str = "en",
) -> str:
    jd_block = (
        job_description.strip()
        if job_description and job_description.strip()
        else "(No job description — evaluate against typical expectations for the role/level.)"
    )
    lang = interview_language_block(locale)

    return f"""Evaluate the candidate's answer.

{lang}

Role: {role}
Level: {level}
Job description (use for alignment scoring when provided):
---
{jd_block}
---

Interview question:
{question}

Candidate answer:
{answer}

Return JSON ONLY:
{{
  "relevance": 0-10,
  "clarity": 0-10,
  "technical_depth": 0-10,
  "communication": 0-10,
  "job_alignment": 0-10,
  "summary": "1-2 sentences",
  "strengths": ["..."],
  "gaps": ["..."],
  "needs_follow_up": true or false,
  "follow_up_hint": "if needs_follow_up, what to probe; else empty string"
}}

If JD is missing, set job_alignment based on general role fit."""


def build_report_prompt(
    role: str,
    level: str,
    job_description: Optional[str],
    qa_block: str,
    locale: str = "en",
) -> str:
    jd_block = (
        job_description.strip()
        if job_description and job_description.strip()
        else "(No job description — report should focus on role/level generically.)"
    )
    lang = interview_language_block(locale)

    return f"""Produce the FINAL interview report for the hiring manager (not shown during the interview).

{lang}

Role: {role}
Level: {level}
Job description:
---
{jd_block}
---

Interview Q&A with per-answer evaluations (JSON):
{qa_block}

Return JSON ONLY:
{{
  "overall_score": 0-100,
  "category_scores": {{
    "technical_depth": 0-100,
    "communication": 0-100,
    "job_fit": 0-100,
    "problem_solving": 0-100
  }},
  "summary": "2-4 sentences overview",
  "strengths": ["..."],
  "weaknesses": ["..."],
  "recommendations": ["..."],
  "vacancy_fit": {{
    "match_percent": 0-100,
    "summary": "how well they match THIS vacancy",
    "requirements_covered_well": ["..."],
    "requirements_gaps": ["..."],
    "topics_to_study": ["..."]
  }},
  "example_strong_answer": "one concise example of a stronger answer pattern for a key gap"
}}

If JD was not provided, vacancy_fit should describe fit to the role/level instead of a specific posting."""


JSON_INSTRUCTION = "Respond with a single JSON object only. No markdown."

# --- Problem / user research interview: human interviews the AI, which plays a user persona ---

PERSONA_KEYS = (
    "tech_employee",
    "retiree",
    "middle_class_messenger",
    "regional_smb",
)


def get_persona_spec(persona: str, locale: str) -> dict:
    """Rich voice / situation for a single character (RU/EN labels + behavior text)."""
    p = (persona or "tech_employee").strip()
    if p not in PERSONA_KEYS:
        p = "tech_employee"
    ru = {
        "tech_employee": {
            "label": "Сотрудник IT-компании",
            "voice": (
                "Ты — респондент, сотрудник крупной IT-компании (офис/гибрид). 30–40 лет, говоришь быстро, с англицизмами, "
                "сравниваешь с конкурентами, важны скорость, удобство, интеграции, иногда перегруз от созвонов. "
                "Можешь ссылаться на «сервис / прод / тикет / ретро», но оставайся в образе «пользуюсь жизнью и сервисами», а не тренер."
            ),
        },
        "retiree": {
            "label": "Пенсионер(ка)",
            "voice": (
                "Ты — пожилой респондент, на пенсии, не всё уверенно в приложениях. Речь спокойная, чуть неторопливая, "
                "может быть лёгкая путаница в терминах, зато честные бытовые детали: деньги, доверие, желание, чтобы «с человеком» или дочь помогла. "
                "Не играй карикатуру — уважительно, правдоподобно."
            ),
        },
        "middle_class_messenger": {
            "label": "Средний класс, бытовые услуги через мессенджер",
            "voice": (
                "Ты — человек 35–50 лет, «нормальный» средний класс: семья, работа, мало времени. Часто заказываешь доставки, врача, мастера, "
                "записи, оплату — через мессенджер или бот, если удобно, иначе раздражаешься от лишних шагов. "
                "Говори о повседневке: курьер, садик, скидка, «напомнили в чате», не о корп. архитектуре."
            ),
        },
        "regional_smb": {
            "label": "Предприниматель (небольшой бизнес в регионе)",
            "voice": (
                "Ты — владелец/менеджер небольшого дела в регионе. Прагматик: срок, цена, налоги, «без сюрпризов», не любишь пустой маркетинг. "
                "Может быть усталость, короткие фразы, 1–2 детали из бизнеса (заказ, поставщик, клиенты)."
            ),
        },
    }
    en = {
        "tech_employee": {
            "label": "Tech company employee",
            "voice": (
                "You are a respondent who works at a big tech company (office/hybrid), ~30–40, fast talk, some tech jargon, "
                "compares options, cares about speed, UX, integrations, sometimes meeting fatigue. Sound like a real person, not a coach."
            ),
        },
        "retiree": {
            "label": "Retiree / pensioner",
            "voice": (
                "You are an older respondent, retired, not fully confident with apps. Calm, a bit slower pace, may fumble terms, "
                "but honest about money, trust, wanting a human on the line or help from a relative. Respectful, not a caricature."
            ),
        },
        "middle_class_messenger": {
            "label": "Middle class — everyday services via messenger",
            "voice": (
                "You are ~35–50, family, busy middle-class life. You order food, book doctors/handymen, pay — via messenger or bots when it saves time; "
                "you get annoyed by extra steps. Talk everyday life, not corporate architecture."
            ),
        },
        "regional_smb": {
            "label": "Small business (regional)",
            "voice": (
                "You are a small-business owner/manager. Pragmatic: time, money, no surprises, short sentences, 1–2 concrete business details."
            ),
        },
    }
    if (locale or "en").strip().lower().startswith("ru"):
        return {**ru[p], "key": p}
    return {**en[p], "key": p}


SYSTEM_PERSONA = """You are a skilled actor simulating exactly ONE end user in a discovery/problem interview.
Rules:
- Stay fully in character for every reply. Do not break the fourth wall (do not say you are an AI, do not offer meta career advice to the "candidate").
- The human is the RESEARCHER / INTERVIEWER; you are the INTERVIEWED user. You never act as the interviewer.
- One natural block of speech per turn (2–5 short paragraphs max). Use first person. Concrete, lived details; emotion allowed.
- Vary: don't repeat the same story beat as in your previous lines; add new detail or a slightly different angle if asked again.
- If the topic/scope (product) is given, anchor your pain points and workarounds to it; otherwise use generic life context that fits the persona.
- Do NOT list bullet-point interview answers like a form — sound like a person talking."""


def build_persona_line_prompt(
    persona: str,
    topic_or_product: str | None,
    transcript_json: str,
    question_index: int,
    min_questions: int,
    max_questions: int,
    last_evaluation_json: str | None,
    locale: str = "en",
) -> str:
    spec = get_persona_spec(persona, locale)
    theme_n = int(question_index) % 5
    extra_angle = [
        "Add a small frustration or workaround.",
        "Mention what you almost did instead.",
        "Name a specific recent situation (vague but believable).",
        "What would make you pay / stay / leave.",
        "How you compare to what a friend or colleague does.",
    ][theme_n]
    top = (topic_or_product or "").strip() or (
        "(No product/topic set — use everyday situations that fit the persona.)"
    )
    lang = interview_language_block(locale)
    prior_qs = _prior_assistant_questions(transcript_json, limit=10)
    anti = ""
    if prior_qs:
        anti = "Lines you (the persona) already said — do NOT parrot them; add NEW detail or a new subtopic each time.\n" + "\n".join(
            f"{i+1}. {q[:500]}" for i, q in enumerate(prior_qs)
        )
    else:
        anti = "This is the OPENING: introduce yourself in character, one concrete slice of your day, and one pain or need — without being asked a question first."

    eval_b = last_evaluation_json or "null"
    is_opening = (question_index == 0) and (not prior_qs or prior_qs == [])

    return f"""Generate the next line of dialogue in a problem / user research interview.

{lang}

{SYSTEM_PERSONA}

Persona: {spec['label']}
How this person speaks and thinks (act this way, do not print this as a list):
{spec['voice']}

Context / product or topic the researcher is exploring (may be empty):
---
{top}
---

Turn rules:
- question_index = number of COMPLETE researcher↔user rounds before this one (0 = you speak first; opening from the persona only).
- Target total turns between {min_questions} and {max_questions} (count each persona reply as one "question" slot in the app).
- If question_index >= {max_questions}, set "interview_complete": true and "question" to a short goodbye IN CHARACTER, then a thank-you line in interview language.
- This turn angle hint: {extra_angle}
- {anti}
- Last researcher's evaluation of THEIR previous question (JSON, helps you calibrate defensiveness / openness; do not quote it aloud):
{eval_b}
- Conversation (JSON [{{"role":"assistant|user","content":"..."}}]) — in THIS mode, **assistant = the persona (you)**, **user = the researcher (human)**:
{transcript_json}

Return JSON ONLY with this exact shape (field name "question" is legacy — here it is always the **persona's next spoken line**):
{{
  "question": "string — the persona's next message only",
  "is_follow_up": true or false,
  "interview_complete": true or false,
  "rationale_internal": "not shown; why this line was chosen"
}}
{"If this is the opening (first assistant message in session), the persona speaks first: daily context + problem hint — 3–5 sentences, no list." if is_opening else "Reply to the researcher's LATEST user message; stay in character; do not ask them a job-interview style question back — you may end with a short question only if it fits naturally."}"""


def build_researcher_question_eval_prompt(
    persona: str,
    topic_or_product: str | None,
    question: str,
    answer: str,
    locale: str = "en",
) -> str:
    """`question` = persona/assistant's last line (context); `answer` = researcher's line to score."""
    spec = get_persona_spec(persona, locale)
    top = (topic_or_product or "").strip() or "(no fixed topic)"
    lang = interview_language_block(locale)
    return f"""The human is doing a PROBLEM / USER research interview. They are the RESEARCHER; the persona is a simulated user.
Evaluate how strong the researcher's LATEST message was — not a job-candidate answer.

{lang}

Persona: {spec['label']}
Topic/product context: {top}

The persona's previous line (context only; do not re-score the persona):
{question}

The researcher's message to score (this is the text to score):
{answer}

Return JSON ONLY, same shape as technical evaluation, but map meaning as follows (0–10 each):
- relevance: how on-topic the question is for learning about the user's problem/behavior
- clarity: is the question clear, one intent, not double-barreled
- technical_depth: depth of inquiry (problem understanding, not programming) — are they going beyond surface?
- communication: empathetic, neutral, not leading, not condescending
- job_alignment: how well the question helps discover needs relevant to the topic/product
- summary: 1–2 sentences
- strengths, gaps, needs_follow_up, follow_up_hint as before (follow-up hint = what a better follow-up could probe)
"""


def build_problem_discovery_report_prompt(
    persona: str,
    topic_or_product: str | None,
    qa_block: str,
    locale: str = "en",
) -> str:
    spec = get_persona_spec(persona, locale)
    top = (topic_or_product or "").strip() or "(no specific product — evaluate discovery quality generically)"
    lang = interview_language_block(locale)
    return f"""Write the FINAL report for a PROBLEM / USER DISCOVERY session (the researcher interviewed a simulated user).

{lang}

Persona: {spec['label']}
Context/topic: {top}

Q&A (each round: researcher question, simulated user answer, evaluation JSON):
{qa_block}

Return JSON ONLY, same top-level structure as a hiring report, but interpret categories for RESEARCH:
- category_scores.technical_depth → depth of your problem/need understanding extracted (rename meaning as problem_depth in your head; still use key technical_depth in JSON for schema stability)
- category_scores.job_fit → alignment of insights to the product/topic
- job_fit, vacancy_fit, etc. = frame as "topic fit" and "insight value", not a job
- example_strong_answer = example of a better **researcher question** the human could have asked
- Make vacancy_fit.match_percent and summary about how strong the *discovery* was and what was learned, not a job match

Keep the exact JSON field names the client expects: overall_score, category_scores, summary, strengths, weaknesses, recommendations, vacancy_fit, example_strong_answer."""
