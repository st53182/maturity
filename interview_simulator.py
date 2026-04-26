"""
AI Interview Simulator — Flask API (MVP).

Endpoints:
  POST /api/interview-simulator/question
  POST /api/interview-simulator/evaluate
  POST /api/interview-simulator/report

Mock when OPENAI_API_KEY is missing or INTERVIEW_SIMULATOR_MOCK=1.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from typing import Any, Optional

from flask import Blueprint, jsonify, request

from interview_simulator_prompts import (
    JSON_INSTRUCTION,
    PERSONA_KEYS,
    SYSTEM_BASE,
    SYSTEM_PERSONA,
    build_evaluate_prompt,
    build_persona_line_prompt,
    build_problem_discovery_report_prompt,
    build_question_prompt,
    build_researcher_question_eval_prompt,
    build_report_prompt,
    get_persona_spec,
)

logger = logging.getLogger(__name__)

bp_interview_simulator = Blueprint("interview_simulator", __name__, url_prefix="/api/interview-simulator")


def _normalize_locale(raw: Any) -> str:
    if not raw or not isinstance(raw, str):
        return "en"
    s = raw.strip().lower().split("-", 1)[0]
    return "ru" if s == "ru" else "en"


def _closing_line(locale: str) -> str:
    return (
        "Спасибо, на этом интервью завершено."
        if locale == "ru"
        else "Thank you — that completes the interview."
    )

MIN_QUESTIONS_DEFAULT = 7
MAX_QUESTIONS_DEFAULT = 13


def _interview_mode(body: dict) -> str:
    raw = body.get("interviewMode") or body.get("interview_mode") or "technical"
    s = str(raw).strip().lower()
    if s in ("problem_user", "problem", "user_research", "discovery", "persona"):
        return "problem_user"
    return "technical"


def _persona_key(body: dict) -> str:
    p = str(body.get("persona") or "tech_employee").strip()
    if p in PERSONA_KEYS:
        return p
    return "tech_employee"


def _mock_mode() -> bool:
    if os.getenv("INTERVIEW_SIMULATOR_MOCK", "").strip().lower() in ("1", "true", "yes"):
        return True
    if not (os.getenv("OPENAI_API_KEY") or "").strip():
        return True
    return False


def _extract_json_object(text: str) -> Optional[dict]:
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}\s*$", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _is_gpt5_model(model: str) -> bool:
    return "gpt-5" in (model or "").strip().lower().split("/")[-1]


def _call_openai(
    user_prompt: str,
    *,
    temperature: float = 0.4,
    max_out_tokens: int = 2000,
    system_content: Optional[str] = None,
) -> str:
    from openai import OpenAI

    timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "120"))
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=timeout)
    model = (os.getenv("INTERVIEW_SIMULATOR_MODEL", "gpt-4.1-mini") or "gpt-4.1-mini").strip()
    sys_msg = system_content if system_content is not None else (SYSTEM_BASE + "\n" + JSON_INSTRUCTION)
    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user_prompt},
    ]
    kwargs: dict = {"model": model, "messages": messages}
    if _is_gpt5_model(model):
        kwargs["max_completion_tokens"] = max_out_tokens
    else:
        kwargs["temperature"] = temperature
        kwargs["max_tokens"] = max_out_tokens
    resp = client.chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()


def _mock_question_payload(body: dict) -> dict:
    idx = int(body.get("questionIndex") or 0)
    max_q = int(body.get("maxQuestions") or MAX_QUESTIONS_DEFAULT)
    loc = _normalize_locale(body.get("locale"))
    jd = (body.get("jobDescription") or "").strip()
    role = body.get("role") or "engineer"
    level = body.get("level") or "middle"
    # questionIndex = completed Q&A rounds; at idx >= max_q there must be no next question
    complete = idx >= max_q
    jd_templates = [
        "[Mock Q{n}] Pick one bullet from the JD and walk through how you would de-risk it before release.",
        "[Mock Q{n}] Choose a stack item mentioned in the JD: what failure mode worries you most and how do you detect it in prod?",
        "[Mock Q{n}] From the JD responsibilities: describe how you would hand off work to another team without losing quality.",
        "[Mock Q{n}] Tie one JD requirement to a concrete metric you would track for 2 weeks after launch.",
        "[Mock Q{n}] Which JD skill is your weakest fit — and how would you close that gap in 30 days?",
    ]
    no_jd_templates = [
        "[Mock Q{n}] ({r}/{l}) Tell me about a production incident: timeline, root cause, and one prevention you added.",
        "[Mock Q{n}] ({r}/{l}) Compare two technical approaches you have used; when would you pick each?",
        "[Mock Q{n}] ({r}/{l}) How do you decide what to test automatically vs manually for a risky change?",
        "[Mock Q{n}] ({r}/{l}) Describe disagreeing with a teammate on design — how did you resolve it?",
        "[Mock Q{n}] ({r}/{l}) What is the hardest performance problem you debugged? What did you measure?",
        "[Mock Q{n}] ({r}/{l}) How do you keep scope under control when stakeholders add \"small\" requests mid-sprint?",
    ]
    if jd:
        tpl = jd_templates[idx % len(jd_templates)]
        q = tpl.format(n=idx + 1)
    else:
        tpl = no_jd_templates[idx % len(no_jd_templates)]
        q = tpl.format(n=idx + 1, r=role, l=level)
    if complete:
        done_msg = (
            "Спасибо — мок-интервью завершено." if loc == "ru" else "Thank you — that completes the mock interview."
        )
        return {
            "question": done_msg,
            "is_follow_up": False,
            "interview_complete": True,
            "question_id": str(uuid.uuid4()),
            "mock": True,
        }
    if loc == "ru":
        if jd:
            q = f"[Мок В{idx + 1}] Возьмите один пункт из описания вакансии и кратко опишите, как вы снизите риски перед релизом."
        else:
            q = (
                f"[Мок В{idx + 1}] Опишите недавний инцидент в проде: что измеряли и какой сделали вывод. "
                f"({role}/{level})"
            )
    return {
        "question": q,
        "is_follow_up": idx % 3 == 2,
        "interview_complete": False,
        "question_id": str(uuid.uuid4()),
        "mock": True,
    }


def _mock_persona_question_payload(body: dict) -> dict:
    """Problem-interview mode: AI plays the user; field 'question' = persona's spoken line."""
    idx = int(body.get("questionIndex") or 0)
    max_q = int(body.get("maxQuestions") or MAX_QUESTIONS_DEFAULT)
    loc = _normalize_locale(body.get("locale"))
    persona = _persona_key(body)
    spec = get_persona_spec(persona, loc)
    topic = (body.get("jobDescription") or "").strip()
    topic_bit = f" ({topic[:100]}…)" if len(topic) > 100 else (f" ({topic})" if topic else "")
    if idx >= max_q:
        done = (
            "На этом у меня всё, спасибо за разговор."
            if loc == "ru"
            else "That's all from me today — thanks for the chat."
        )
        return {
            "question": done,
            "is_follow_up": False,
            "interview_complete": True,
            "question_id": str(uuid.uuid4()),
            "mock": True,
        }
    is_ru = loc == "ru"
    if is_ru:
        tword = topic.split()[0] if topic else "это"
        seq = [
            f"[Мок-реплика {idx + 1}] Добрый день. Немного о себе как о {spec['label']}{topic_bit}. "
            f"Вчера снова пришлось обходить косяк в сервисе — короче, бесит, когда не с первого клика.",
            f"Если копнёте — мне важно, чтобы {tword} не съедало вечер мелкими кусками, когда уже устал.",
            f"Сравнивал с тем, что подсказала сестра в чате: у неё тоже не всё гладко, зато она в любом случае добьётся, если сбой.",
            f"Заплатил бы больше, если бы сразу было прозрачно и без сюрпризов — а так я ищу обходы.",
        ]
    else:
        seq = [
            f"[Mock line {idx + 1}] Hi — I’m the {spec['label']}{topic_bit}. Yesterday I had to work around a glitch again; "
            f"I get annoyed when it’s not one-tap easy.",
            f"I’m not looking for ‘perfect’ — I need this not to eat my evening in tiny chunks when I’m already tired.",
            f"My friend in chat had a different workaround — not smoother, but at least predictable.",
            f"I’d pay more for clarity and no surprise fees, but for now I keep juggling apps.",
        ]
    q = seq[idx % len(seq)]
    return {
        "question": q,
        "is_follow_up": idx > 0 and idx % 4 == 2,
        "interview_complete": False,
        "question_id": str(uuid.uuid4()),
        "mock": True,
    }


def _mock_evaluate_payload(locale: str = "en") -> dict:
    if locale == "ru":
        return {
            "relevance": 7,
            "clarity": 7,
            "technical_depth": 6,
            "communication": 8,
            "job_alignment": 6,
            "summary": "Мок-оценка: ответ правдоподобен, но не хватает конкретики и метрик.",
            "strengths": ["Структурированный ответ", "Понятная коммуникация"],
            "gaps": ["Мало глубины по краевым случаям", "Нет конкретных метрик"],
            "needs_follow_up": True,
            "follow_up_hint": "Попросите пример с измеримым результатом.",
            "mock": True,
        }
    return {
        "relevance": 7,
        "clarity": 7,
        "technical_depth": 6,
        "communication": 8,
        "job_alignment": 6,
        "summary": "Mock evaluation: answer is plausible but could use more specifics and metrics.",
        "strengths": ["Structured response", "Clear communication"],
        "gaps": ["Limited depth on edge cases", "No concrete metrics"],
        "needs_follow_up": True,
        "follow_up_hint": "Ask for a concrete example with measurable outcome.",
        "mock": True,
    }


def _mock_problem_report_payload(body: dict) -> dict:
    loc = _normalize_locale(body.get("locale"))
    persona = _persona_key(body)
    spec = get_persona_spec(persona, loc)
    topic = (body.get("jobDescription") or "").strip()
    if loc == "ru":
        return {
            "overall_score": 74,
            "category_scores": {
                "technical_depth": 72,
                "communication": 78,
                "job_fit": 70,
                "problem_solving": 73,
            },
            "summary": f"Мок-отчёт: выявлены реальные сценарии и боли; для {spec['label']} — проверьте доверие и простоту. Тема: {topic or 'без уточнения'}.",
            "strengths": ["Сцены и эмоции", "Сравнения с обходами"],
            "weaknesses": ["Мало количественных деталей", "Почти нет валидации гипотез"],
            "recommendations": [
                "Следующий шаг: проверка с 3–5 респондентами в той же нише.",
                "Зафиксировать топ-3 боли и критерии «готовы платить / уйдём к конкуренту».",
            ],
            "vacancy_fit": {
                "match_percent": 70,
                "summary": f"Сила инсайтов относительно темы; мок-данные, персона: {spec['label']}.",
                "requirements_covered_well": ["Сценарии", "триггеры раздражения", "workaround"],
                "requirements_gaps": ["Сегменты, метрики, частоты", "A/B-намерение"],
                "topics_to_study": ["Повторяемые триггеры", "критерии доверия", "сравнение с альтернативами"],
            },
            "example_strong_answer": "Расскажите про последний раз, когда вы отказались пройти сценарий: что нажимали, что ожидали, сколько ушло времени?",
            "mock": True,
        }
    return {
        "overall_score": 74,
        "category_scores": {
            "technical_depth": 72,
            "communication": 78,
            "job_fit": 70,
            "problem_solving": 73,
        },
        "summary": f"Mock: scenarios and pains surfaced; for {spec['label']}, test trust and simplicity. Topic: {topic or 'n/a'}.",
        "strengths": ["Concrete scenes", "workarounds"],
        "weaknesses": ["Few numeric anchors", "little hypothesis testing"],
        "recommendations": [
            f"Next: validate with 3–5 more people who match the {spec['key']} pattern.",
            "Capture top pains and 'would pay / would churn' criteria.",
        ],
        "vacancy_fit": {
            "match_percent": 70,
            "summary": f"Mock insight value vs. topic; persona: {spec['label']}.",
            "requirements_covered_well": ["Scenes", "frustration", "workarounds"],
            "requirements_gaps": ["Frequency", "willingness to pay", "alternatives used"],
            "topics_to_study": ["Trust cues", "comparison shopping", "repeat triggers"],
        },
        "example_strong_answer": "Walk me through the last time you gave up: what you tapped, what you expected, and how long it took.",
        "mock": True,
    }


def _mock_report_payload(body: dict) -> dict:
    if _interview_mode(body) == "problem_user":
        return _mock_problem_report_payload(body)
    jd = (body.get("jobDescription") or "").strip()
    loc = _normalize_locale(body.get("locale"))
    if loc == "ru":
        return {
            "overall_score": 72,
            "category_scores": {
                "technical_depth": 68,
                "communication": 80,
                "job_fit": 70 if jd else 65,
                "problem_solving": 72,
            },
            "summary": "Мок-отчёт: хорошая коммуникация; углубите системный дизайн и темы из вакансии.",
            "strengths": ["Понятные объяснения", "Совместный тон"],
            "weaknesses": ["Мало глубины по масштабированию", "Мало конкретных примеров"],
            "recommendations": [
                "Потренируйте STAR-истории под пункты вакансии.",
                "Проработайте один глубокий разбор основного стека из вакансии.",
            ],
            "vacancy_fit": {
                "match_percent": 68 if jd else 60,
                "summary": (
                    "Умеренное соответствие роли; мок-данные — связывайте ответы с каждым пунктом вакансии."
                    if jd
                    else "Общее соответствие уровню; добавьте описание вакансии для точной оценки."
                ),
                "requirements_covered_well": ["Коммуникация", "Ответственность"] if jd else ["База"],
                "requirements_gaps": ["Глубина по стеку из вакансии", "Эксплуатация в проде"] if jd else ["Глубина"],
                "topics_to_study": ["Системный дизайн", "Стратегия тестирования", "Наблюдаемость"],
            },
            "example_strong_answer": (
                "Я бы назвал конкретный сервис, SLA, сценарий отказа, метрики, которые смотрели, и план отката."
            ),
            "mock": True,
        }
    return {
        "overall_score": 72,
        "category_scores": {
            "technical_depth": 68,
            "communication": 80,
            "job_fit": 70 if jd else 65,
            "problem_solving": 72,
        },
        "summary": "Mock report: solid communication; deepen system design and JD-specific stack topics.",
        "strengths": ["Clear explanations", "Collaborative tone"],
        "weaknesses": ["Limited depth on scalability", "Few concrete examples"],
        "recommendations": [
            "Practice STAR stories tied to JD requirements.",
            "Drill one deep dive on the primary stack from the JD.",
        ],
        "vacancy_fit": {
            "match_percent": 68 if jd else 60,
            "summary": (
                "Reasonable fit for the role; mock data — connect answers to each JD bullet when JD is provided."
                if jd
                else "General role fit; add a JD for vacancy-specific scoring."
            ),
            "requirements_covered_well": ["Communication", "Ownership mindset"] if jd else ["Basics"],
            "requirements_gaps": ["Depth on listed stack", "Production operations"] if jd else ["Depth"],
            "topics_to_study": ["System design", "Testing strategy", "Observability"],
        },
        "example_strong_answer": (
            "I would cite a specific service, the SLA, the failure mode, metrics we tracked, and the rollback plan."
        ),
        "mock": True,
    }


@bp_interview_simulator.route("/question", methods=["POST"])
def post_question():
    try:
        body = request.get_json(force=True, silent=True) or {}
        mode = _interview_mode(body)
        role = (body.get("role") or "software_engineer").strip()
        level = (body.get("level") or "middle").strip()
        job_description = body.get("jobDescription")
        transcript = body.get("transcript") or []
        question_index = int(body.get("questionIndex") or 0)
        min_q = int(body.get("minQuestions") or MIN_QUESTIONS_DEFAULT)
        max_q = int(body.get("maxQuestions") or MAX_QUESTIONS_DEFAULT)
        last_eval = body.get("lastEvaluation")
        locale = _normalize_locale(body.get("locale"))

        # Hard cap: client sends questionIndex = len(completed rounds); no further questions past max_q
        if question_index >= max_q:
            return jsonify(
                {
                    "success": True,
                    "question": _closing_line(locale),
                    "is_follow_up": False,
                    "interview_complete": True,
                    "question_id": str(uuid.uuid4()),
                }
            ), 200

        if _mock_mode():
            out = _mock_persona_question_payload(body) if mode == "problem_user" else _mock_question_payload(body)
            return jsonify({"success": True, **out}), 200

        transcript_json = json.dumps(transcript, ensure_ascii=False)
        last_eval_json = json.dumps(last_eval, ensure_ascii=False) if last_eval is not None else None
        try:
            q_temp = float(os.getenv("INTERVIEW_SIMULATOR_QUESTION_TEMP", "0.68"))
        except ValueError:
            q_temp = 0.68
        q_temp = max(0.0, min(1.5, q_temp))

        if mode == "problem_user":
            persona = _persona_key(body)
            user_prompt = build_persona_line_prompt(
                persona=persona,
                topic_or_product=job_description if isinstance(job_description, str) else None,
                transcript_json=transcript_json,
                question_index=question_index,
                min_questions=min_q,
                max_questions=max_q,
                last_evaluation_json=last_eval_json,
                locale=locale,
            )
            raw = _call_openai(
                user_prompt,
                temperature=q_temp,
                system_content=SYSTEM_PERSONA + "\n" + JSON_INSTRUCTION,
            )
        else:
            user_prompt = build_question_prompt(
                role=role,
                level=level,
                job_description=job_description if isinstance(job_description, str) else None,
                transcript_json=transcript_json,
                question_index=question_index,
                min_questions=min_q,
                max_questions=max_q,
                last_evaluation_json=last_eval_json,
                locale=locale,
            )
            raw = _call_openai(user_prompt, temperature=q_temp)
        data = _extract_json_object(raw)
        if not data or "question" not in data:
            logger.warning("Bad question JSON: %s", raw[:500])
            return jsonify({"success": False, "error": "Invalid AI response"}), 502

        data.setdefault("is_follow_up", False)
        data.setdefault("interview_complete", False)
        data["question_id"] = str(uuid.uuid4())
        return jsonify({"success": True, **data}), 200
    except Exception as e:
        logger.exception("post_question: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@bp_interview_simulator.route("/evaluate", methods=["POST"])
def post_evaluate():
    try:
        body = request.get_json(force=True, silent=True) or {}
        mode = _interview_mode(body)
        role = (body.get("role") or "software_engineer").strip()
        level = (body.get("level") or "middle").strip()
        job_description = body.get("jobDescription")
        question = (body.get("question") or "").strip()
        answer = (body.get("answer") or "").strip()
        if not question or not answer:
            return jsonify({"success": False, "error": "question and answer required"}), 400

        locale = _normalize_locale(body.get("locale"))

        if _mock_mode():
            return jsonify({"success": True, "evaluation": _mock_evaluate_payload(locale)}), 200

        if mode == "problem_user":
            persona = _persona_key(body)
            user_prompt = build_researcher_question_eval_prompt(
                persona=persona,
                topic_or_product=job_description if isinstance(job_description, str) else None,
                question=question,
                answer=answer,
                locale=locale,
            )
        else:
            user_prompt = build_evaluate_prompt(
                role=role,
                level=level,
                job_description=job_description if isinstance(job_description, str) else None,
                question=question,
                answer=answer,
                locale=locale,
            )
        raw = _call_openai(user_prompt)
        data = _extract_json_object(raw)
        if not data or "relevance" not in data:
            logger.warning("Bad evaluate JSON: %s", raw[:500])
            return jsonify({"success": False, "error": "Invalid AI response"}), 502

        return jsonify({"success": True, "evaluation": data}), 200
    except Exception as e:
        logger.exception("post_evaluate: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@bp_interview_simulator.route("/report", methods=["POST"])
def post_report():
    try:
        body = request.get_json(force=True, silent=True) or {}
        mode = _interview_mode(body)
        role = (body.get("role") or "software_engineer").strip()
        level = (body.get("level") or "middle").strip()
        job_description = body.get("jobDescription")
        rounds = body.get("rounds")
        if not isinstance(rounds, list) or not rounds:
            return jsonify({"success": False, "error": "rounds array required"}), 400

        locale = _normalize_locale(body.get("locale"))

        if _mock_mode():
            return jsonify({"success": True, "report": _mock_report_payload(body)}), 200

        qa_block = json.dumps(rounds, ensure_ascii=False)
        if mode == "problem_user":
            persona = _persona_key(body)
            user_prompt = build_problem_discovery_report_prompt(
                persona=persona,
                topic_or_product=job_description if isinstance(job_description, str) else None,
                qa_block=qa_block,
                locale=locale,
            )
        else:
            user_prompt = build_report_prompt(
                role=role,
                level=level,
                job_description=job_description if isinstance(job_description, str) else None,
                qa_block=qa_block,
                locale=locale,
            )
        raw = _call_openai(user_prompt)
        data = _extract_json_object(raw)
        if not data or "overall_score" not in data:
            logger.warning("Bad report JSON: %s", raw[:500])
            return jsonify({"success": False, "error": "Invalid AI response"}), 502

        return jsonify({"success": True, "report": data}), 200
    except Exception as e:
        logger.exception("post_report: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@bp_interview_simulator.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "mock": _mock_mode()}), 200
