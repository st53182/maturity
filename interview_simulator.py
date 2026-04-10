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
    SYSTEM_BASE,
    build_evaluate_prompt,
    build_question_prompt,
    build_report_prompt,
)

logger = logging.getLogger(__name__)

bp_interview_simulator = Blueprint("interview_simulator", __name__, url_prefix="/api/interview-simulator")

MIN_QUESTIONS_DEFAULT = 7
MAX_QUESTIONS_DEFAULT = 13


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


def _call_openai(user_prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("INTERVIEW_SIMULATOR_MODEL", "gpt-4.1-mini")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_BASE + "\n" + JSON_INSTRUCTION},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=2000,
    )
    return (resp.choices[0].message.content or "").strip()


def _mock_question_payload(body: dict) -> dict:
    idx = int(body.get("questionIndex") or 0)
    jd = (body.get("jobDescription") or "").strip()
    role = body.get("role") or "engineer"
    level = body.get("level") or "middle"
    complete = idx >= MAX_QUESTIONS_DEFAULT - 1
    if jd:
        q = (
            f"[Mock Q{idx + 1}] For this role at {level} level: pick one concrete requirement from the JD "
            "and explain how you would validate delivery quality in production."
        )
    else:
        q = f"[Mock Q{idx + 1}] ({role}/{level}) Describe a recent technical decision you owned and the trade-offs."
    if complete:
        return {
            "question": "Thank you — that completes the mock interview.",
            "is_follow_up": False,
            "interview_complete": True,
            "question_id": str(uuid.uuid4()),
            "mock": True,
        }
    return {
        "question": q,
        "is_follow_up": idx % 3 == 2,
        "interview_complete": False,
        "question_id": str(uuid.uuid4()),
        "mock": True,
    }


def _mock_evaluate_payload() -> dict:
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


def _mock_report_payload(body: dict) -> dict:
    jd = (body.get("jobDescription") or "").strip()
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
        role = (body.get("role") or "software_engineer").strip()
        level = (body.get("level") or "middle").strip()
        job_description = body.get("jobDescription")
        transcript = body.get("transcript") or []
        question_index = int(body.get("questionIndex") or 0)
        min_q = int(body.get("minQuestions") or MIN_QUESTIONS_DEFAULT)
        max_q = int(body.get("maxQuestions") or MAX_QUESTIONS_DEFAULT)
        last_eval = body.get("lastEvaluation")

        if _mock_mode():
            out = _mock_question_payload(body)
            return jsonify({"success": True, **out}), 200

        transcript_json = json.dumps(transcript, ensure_ascii=False)
        last_eval_json = json.dumps(last_eval, ensure_ascii=False) if last_eval is not None else None
        user_prompt = build_question_prompt(
            role=role,
            level=level,
            job_description=job_description if isinstance(job_description, str) else None,
            transcript_json=transcript_json,
            question_index=question_index,
            min_questions=min_q,
            max_questions=max_q,
            last_evaluation_json=last_eval_json,
        )
        raw = _call_openai(user_prompt)
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
        role = (body.get("role") or "software_engineer").strip()
        level = (body.get("level") or "middle").strip()
        job_description = body.get("jobDescription")
        question = (body.get("question") or "").strip()
        answer = (body.get("answer") or "").strip()
        if not question or not answer:
            return jsonify({"success": False, "error": "question and answer required"}), 400

        if _mock_mode():
            return jsonify({"success": True, "evaluation": _mock_evaluate_payload()}), 200

        user_prompt = build_evaluate_prompt(
            role=role,
            level=level,
            job_description=job_description if isinstance(job_description, str) else None,
            question=question,
            answer=answer,
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
        role = (body.get("role") or "software_engineer").strip()
        level = (body.get("level") or "middle").strip()
        job_description = body.get("jobDescription")
        rounds = body.get("rounds")
        if not isinstance(rounds, list) or not rounds:
            return jsonify({"success": False, "error": "rounds array required"}), 400

        if _mock_mode():
            return jsonify({"success": True, "report": _mock_report_payload(body)}), 200

        qa_block = json.dumps(rounds, ensure_ascii=False)
        user_prompt = build_report_prompt(
            role=role,
            level=level,
            job_description=job_description if isinstance(job_description, str) else None,
            qa_block=qa_block,
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
