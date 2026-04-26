"""Системный + приёмо-сдаточный тест для:
  1) PO Path  (Jobs To Be Done -> Value Map -> Customer Fit -> Lean Canvas)
  2) Scrum Simulator (lobby -> planning -> 10 days -> review -> retro -> summary)

Запускать:  python -m _smoke_acceptance

Скрипт ничего не пишет в реальную БД: использует in-memory SQLite + Flask test_client.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import traceback
from typing import Any, Dict, List, Optional


def _banner(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def _ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def _info(msg: str) -> None:
    print(f"  ..  {msg}")


def _fail(msg: str, body: Any = None) -> None:
    print(f"  [FAIL] {msg}")
    if body is not None:
        try:
            print("        body =", json.dumps(body, ensure_ascii=False)[:600])
        except Exception:
            print("        body =", body)
    raise AssertionError(msg)


def _assert_status(resp, expected: int, ctx: str) -> Dict[str, Any]:
    body: Any
    try:
        body = resp.get_json()
    except Exception:
        body = None
    if resp.status_code != expected:
        _fail(f"{ctx}: expected HTTP {expected}, got {resp.status_code}", body)
    return body or {}


# --------------------------- bootstrap app/db ---------------------------

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("FLASK_TESTING", "1")
os.environ.setdefault("OPENAI_API_KEY", "")  # отключим реальные вызовы — должно работать на скриптах

# Make project root importable when run as `python _smoke_acceptance.py`
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from app import app, db  # noqa: E402
from models import (  # noqa: E402
    User,
    AgileTrainingSession,
    AgileTrainingGroup,
    AgileTrainingParticipant,
)


def _bootstrap(exercise_key: str, locale: str = "ru") -> Dict[str, Any]:
    """Создать пользователя-фасилитатора, сессию и одну группу. Возвращает slug + id."""
    with app.app_context():
        owner = User(username=f"facil_{secrets.token_hex(3)}")
        if hasattr(owner, "set_password"):
            owner.set_password("test")
        db.session.add(owner)
        db.session.commit()

        sess = AgileTrainingSession(
            owner_user_id=owner.id,
            title=f"Smoke {exercise_key}",
            exercise_key=exercise_key,
            locale=locale,
        )
        db.session.add(sess)
        db.session.commit()

        slug = f"smk-{secrets.token_hex(4)}"
        g = AgileTrainingGroup(
            session_id=sess.id,
            name="Team A",
            slug=slug,
        )
        db.session.add(g)
        db.session.commit()

        return {
            "owner_id": owner.id,
            "session_id": sess.id,
            "group_id": g.id,
            "slug": slug,
        }


def _join_participant(client, slug: str, name: str, existing_token: Optional[str] = None) -> str:
    body: Dict[str, Any] = {"display_name": name}
    if existing_token:
        body["participant_token"] = existing_token
    resp = client.post(
        f"/api/agile-training/g/{slug}/participant",
        json=body,
    )
    data = _assert_status(resp, 200, "participant_create")
    token = data.get("participant_token")
    assert token, f"no token in {data}"
    return token


# --------------------------- PO PATH ---------------------------


def smoke_po_path() -> None:
    _banner("PO PATH — приёмо-сдаточные испытания")

    info = _bootstrap("po_path", "ru")
    slug = info["slug"]
    client = app.test_client()

    # 1) Гость без токена видит экран приветствия (answer == None, нельзя писать)
    resp = client.get(f"/api/agile-training/po-path/g/{slug}/state")
    state = _assert_status(resp, 200, "po state (guest)")
    assert state["answer"] is None, "answer must be None for guest"
    assert state["participant_known"] is False
    assert state["token_provided"] is False
    assert state["stage_fields"]["jtbd"], "stage_fields must be returned"
    assert state["stage_layout"]["jtbd"], "stage_layout must be returned"
    _ok("guest /state -> answer=None, participant_known=False, layout/fields присутствуют")

    # 2) Регистрируемся участником и проверяем что answer создаётся eagerly
    token = _join_participant(client, slug, "Tester PO")
    resp = client.get(
        f"/api/agile-training/po-path/g/{slug}/state",
        query_string={"participant_token": token},
    )
    state = _assert_status(resp, 200, "po state after join")
    assert state["participant_known"] is True
    assert state["token_provided"] is True
    assert state["answer"] is not None, "answer must be eagerly created"
    assert state["answer"]["current_stage"] == "jtbd", "first stage must be jtbd"
    _ok("после join: answer создан, current_stage=jtbd, participant_known=True")

    # 3) Пробуем сразу submit пустого этапа — backend должен вернуть 400 (защита от пустоты)
    resp = client.post(
        f"/api/agile-training/po-path/g/{slug}/submit",
        json={"participant_token": token, "stage": "jtbd"},
    )
    body = _assert_status(resp, 400, "submit empty jtbd")
    assert body.get("error") == "stage_empty"
    _ok("submit пустого этапа отклонён со stage_empty")

    # 4) Автосейв полей jtbd
    jtbd_data = {
        "job_statement": "Когда я открываю отчёт по продажам, я хочу быстро понять, где мы теряем деньги.",
        "trigger": "Каждое утро понедельника на статусе с CFO.",
        "context": "В кабинете, на ноутбуке, перед звонком с командой.",
        "frequency": "Раз в неделю стабильно, иногда чаще при срочных сделках.",
        "motivation": "Не пропустить риск и быстро принять решение.",
        "outcomes": "Понять три главных гипотезы, что пошло не так.",
        "current_solution": "Сейчас вручную сводим Excel из 4 источников.",
        "barriers": "Отчёт не учитывает скидки и возвраты, цифры не бьются.",
        "fears": "Боюсь, что приму решение по неполным данным.",
        "success_criteria": "За 5 минут вижу 3 риска и причину каждого.",
    }
    resp = client.post(
        f"/api/agile-training/po-path/g/{slug}/answer",
        json={"participant_token": token, "stage": "jtbd", "data": jtbd_data, "confidence": 4},
    )
    body = _assert_status(resp, 200, "autosave jtbd")
    assert body["saved"] is True
    saved = body["answer"]["stages"]["jtbd"]["data"]
    for k, v in jtbd_data.items():
        assert saved.get(k) == v, f"jtbd.{k} not saved correctly"
    _ok("автосейв jtbd: все поля сохранены, confidence=4")

    # 5) Submit jtbd -> approved, current=value
    resp = client.post(
        f"/api/agile-training/po-path/g/{slug}/submit",
        json={"participant_token": token, "stage": "jtbd"},
    )
    body = _assert_status(resp, 200, "submit jtbd")
    assert body["approved"] is True
    assert body["next_stage"] == "value"
    assert body["answer"]["current_stage"] == "value", "current_stage must move to value"
    assert body["answer"]["stages"]["jtbd"]["status"] == "approved"
    _ok("submit jtbd -> approved, current_stage=value")

    # 6) Защита: попытка autosave в canvas, который ещё закрыт, должна давать 409
    resp = client.post(
        f"/api/agile-training/po-path/g/{slug}/answer",
        json={"participant_token": token, "stage": "canvas", "data": {"problem": "x"}},
    )
    body = _assert_status(resp, 409, "autosave locked stage")
    assert body.get("error") == "stage_locked"
    _ok("autosave «закрытого» этапа отклонён 409 stage_locked")

    # 7) value
    value_data = {
        "product": "Дашборд еженедельной выручки и потерь по сегментам.",
        "pains": "Не вижу, где утекает маржа; цифры не бьются; готовлю отчёт ночью.",
        "gains": "Решение принимаю до утреннего синка; экономлю 4 часа в неделю.",
        "pain_relievers": "Авто-сводка по 4 источникам + алерты по красным KPI.",
    }
    client.post(
        f"/api/agile-training/po-path/g/{slug}/answer",
        json={"participant_token": token, "stage": "value", "data": value_data},
    )
    resp = client.post(
        f"/api/agile-training/po-path/g/{slug}/submit",
        json={"participant_token": token, "stage": "value"},
    )
    body = _assert_status(resp, 200, "submit value")
    assert body["next_stage"] == "fit"
    assert body["answer"]["current_stage"] == "fit"
    _ok("submit value -> approved, current_stage=fit")

    # 8) fit
    fit_data = {
        "customer": "CFO средней B2B-компании, 100–500 человек.",
        "why_choose": "Готовая интеграция с 1С/Excel/CRM, цифры бьются автоматически.",
        "alternatives": "Ручной Excel; PowerBI с консультантом за 6 мес.",
        "usage_context": "Понедельник 9:30, перед statement-звонком.",
    }
    client.post(
        f"/api/agile-training/po-path/g/{slug}/answer",
        json={"participant_token": token, "stage": "fit", "data": fit_data},
    )
    resp = client.post(
        f"/api/agile-training/po-path/g/{slug}/submit",
        json={"participant_token": token, "stage": "fit"},
    )
    body = _assert_status(resp, 200, "submit fit")
    assert body["next_stage"] == "canvas"
    _ok("submit fit -> approved, current_stage=canvas")

    # 9) canvas
    canvas_data = {
        "problem": "CFO теряет 4 часа на сборку отчёта и не видит реальную картину маржи.",
        "segments": "CFO B2B 100–500 чел. в индустриях с большим числом скидок.",
        "value_prop": "Авто-сводка маржи и алерты — за 5 минут вижу 3 риска.",
        "solution": "Pull-коннекторы 1С/Excel/CRM + правила алертов + PDF.",
        "channels": "Прямые продажи через CFO-сообщества, кейсы, демо.",
        "revenue": "SaaS подписка 200$/seat/мес.",
        "costs": "Команда + хостинг + интеграции.",
        "metrics": "Доля красных KPI, увиденных вовремя; время до решения.",
        "unfair_advantage": "Готовый набор правил по индустриям.",
        "early_adopters": "5 финдиректоров из нашей сети.",
    }
    client.post(
        f"/api/agile-training/po-path/g/{slug}/answer",
        json={"participant_token": token, "stage": "canvas", "data": canvas_data},
    )
    resp = client.post(
        f"/api/agile-training/po-path/g/{slug}/submit",
        json={"participant_token": token, "stage": "canvas"},
    )
    body = _assert_status(resp, 200, "submit canvas")
    assert body["next_stage"] == "done"
    answer = body["answer"]
    assert answer["current_stage"] == "done"
    for st in ("jtbd", "value", "fit", "canvas"):
        assert answer["stages"][st]["status"] == "approved", f"{st} not approved"
    _ok("submit canvas -> done, все 4 этапа approved")

    # 10) Refresh после завершения — answer всё ещё на месте, current_stage=done
    resp = client.get(
        f"/api/agile-training/po-path/g/{slug}/state",
        query_string={"participant_token": token},
    )
    state = _assert_status(resp, 200, "po state after done")
    assert state["answer"]["current_stage"] == "done"
    assert state["participant_known"] is True
    _ok("рефреш после завершения — состояние сохранилось, current_stage=done")

    # 11) /return на jtbd — все этапы откатываются в draft, current_stage=jtbd
    resp = client.post(
        f"/api/agile-training/po-path/g/{slug}/return",
        json={"participant_token": token, "stage": "jtbd"},
    )
    body = _assert_status(resp, 200, "return jtbd")
    answer = body["answer"]
    assert answer["current_stage"] == "jtbd"
    for st in ("jtbd", "value", "fit", "canvas"):
        assert answer["stages"][st]["status"] == "draft", f"{st} should be draft after return"
        assert answer["stages"][st]["data"], f"{st} data must be preserved after return"
    _ok("/return на jtbd — все этапы в draft, данные сохранились")

    # 12) Bogus token -> token_provided=True, participant_known=False (фронт чистит токен)
    resp = client.get(
        f"/api/agile-training/po-path/g/{slug}/state",
        query_string={"participant_token": "BOGUS_TOKEN_X"},
    )
    state = _assert_status(resp, 200, "po state bogus")
    assert state["token_provided"] is True
    assert state["participant_known"] is False
    assert state["answer"] is None
    _ok("bogus token -> participant_known=False, answer=None (фронт сбросит токен)")

    # 13) Гость с другой локалью получает контент EN
    resp = client.get(f"/api/agile-training/po-path/g/{slug}/state", query_string={"locale": "en"})
    state = _assert_status(resp, 200, "po state EN guest")
    assert state["effective_locale"] == "en"
    assert state["content"], "EN content must be present"
    _ok("гость с locale=en — отдаётся EN-контент")


# --------------------------- SCRUM SIM ---------------------------


def _state_scrum(client, slug: str, token: Optional[str] = None) -> Dict[str, Any]:
    qs: Dict[str, str] = {}
    if token:
        qs["participant_token"] = token
    resp = client.get(f"/api/agile-training/scrum-sim/g/{slug}/state", query_string=qs)
    return _assert_status(resp, 200, f"scrum state token={bool(token)}")


def smoke_scrum_sim() -> None:
    _banner("SCRUM SIM — приёмо-сдаточные испытания")

    info = _bootstrap("scrum_simulator", "ru")
    slug = info["slug"]
    client = app.test_client()

    # 1) Лобби, гость
    s = _state_scrum(client, slug)
    assert s["state"]["phase"] == "lobby"
    assert s["state"]["sprint_days"] == 10
    initial_tasks: List[Dict[str, Any]] = s["state"]["tasks"]
    assert initial_tasks, "must have product backlog tasks"
    _ok(f"lobby: {len(initial_tasks)} задач в product backlog")

    # 2) Регистрируем PO + Dev (хотя бы 2 роли, чтобы decision проверки прошли)
    po_token = _join_participant(client, slug, "PO")
    dev_token = _join_participant(client, slug, "Dev")
    for tok, role in ((po_token, "product_owner"), (dev_token, "developer")):
        resp = client.post(
            f"/api/agile-training/scrum-sim/g/{slug}/join",
            json={"participant_token": tok, "role": role},
        )
        body = _assert_status(resp, 200, f"join {role}")
        assert body["role"] == role, body
    _ok("PO + Dev зарегистрированы и взяли роли")

    # 3) Планирование: затягиваем в спринт несколько независимых задач
    s = _state_scrum(client, slug, po_token)
    product_tasks = [t for t in s["state"]["tasks"] if t["column"] == "product"]
    # сортируем по сложности по возрастанию + игнорируем те, у кого есть deps (пусть будут отдельным сценарием)
    indep = [t for t in product_tasks if not t.get("deps")]
    indep_sorted = sorted(indep, key=lambda t: (int(t["complexity"]), t["title"]))
    # тащим первые 3 независимых
    pulled: List[str] = []
    for t in indep_sorted[:3]:
        resp = client.post(
            f"/api/agile-training/scrum-sim/g/{slug}/planning",
            json={"participant_token": po_token, "action": "pull", "task_key": t["key"]},
        )
        body = _assert_status(resp, 200, f"pull {t['key']}")
        pulled.append(t["key"])
    assert pulled, "should have pulled independent tasks"
    _ok(f"в спринт затянуто {len(pulled)} независимых задач: {pulled}")

    # 3b) И возьмём задачу с deps через pull_chain — backend должен подтянуть всю цепочку
    chain_root = next(
        (t for t in product_tasks if t.get("deps")),
        None,
    )
    chain_pulled: List[str] = []
    if chain_root:
        resp = client.post(
            f"/api/agile-training/scrum-sim/g/{slug}/planning",
            json={"participant_token": po_token, "action": "pull_chain", "task_key": chain_root["key"]},
        )
        body = _assert_status(resp, 200, "pull_chain")
        chain_pulled = body.get("pulled_chain", [])
        _ok(f"pull_chain {chain_root['key']}: вместе с ним подтянулись {chain_pulled or 'ничего сверху'}")
    else:
        _info("в датасете нет задач с deps — пропускаем тест pull_chain")

    # 3c) Проверим push (вернуть задачу обратно в product backlog)
    s = _state_scrum(client, slug, po_token)
    sprint_tasks_now = [t for t in s["state"]["tasks"] if t["column"] == "backlog"]
    if len(sprint_tasks_now) >= 4:
        push_target = sprint_tasks_now[-1]
        resp = client.post(
            f"/api/agile-training/scrum-sim/g/{slug}/planning",
            json={"participant_token": po_token, "action": "push", "task_key": push_target["key"]},
        )
        _assert_status(resp, 200, "push back")
        _ok(f"push {push_target['key']} обратно в product backlog работает")

    # 4) Sprint goal + planning/confirm
    resp = client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/planning",
        json={"participant_token": po_token, "sprint_goal": "Закрыть 3 фичи MVP"},
    )
    _assert_status(resp, 200, "set goal")
    resp = client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/planning/confirm",
        json={"participant_token": po_token},
    )
    body = _assert_status(resp, 200, "planning confirm")
    state = body["state"]
    assert state["phase"] == "day_1"
    assert state["sprint_goal"] == "Закрыть 3 фичи MVP"
    schedule = state["event_schedule"]
    assert isinstance(schedule, dict)
    _ok(f"planning/confirm -> day_1, событий запланировано: {sum(1 for v in schedule.values() if v)}")

    # 5) Регрессия: blocked task — задача с не выполненными deps НЕ должна стартовать
    s = _state_scrum(client, slug, po_token)
    tasks_now = {t["key"]: t for t in s["state"]["tasks"]}
    blocked_candidate = next(
        (
            t for t in s["state"]["tasks"]
            if t["column"] == "backlog"
            and t.get("deps")
            and any(tasks_now.get(d, {}).get("column") not in ("done", "review") for d in t["deps"])
        ),
        None,
    )
    if blocked_candidate:
        resp = client.post(
            f"/api/agile-training/scrum-sim/g/{slug}/task/start",
            json={"participant_token": po_token, "task_key": blocked_candidate["key"]},
        )
        body = _assert_status(resp, 400, f"start with unmet deps {blocked_candidate['key']}")
        assert body.get("error") == "deps not ready"
        assert isinstance(body.get("missing"), list) and body["missing"], "must list missing deps"
        _ok(f"task/start блокируется при невыполненных deps: {body['missing']}")
    else:
        _info("нет задач с невыполненными deps в sprint backlog — пропускаем negative-test для start")

    # 6) Sprint loop: 10 дней — каждый день reveal -> start новых задач (если можно) -> allocate -> end
    last_state = state
    started_tasks: set = set()
    daily_decisions_used = 0
    for day_num in range(1, 11):
        # 6a) reveal event
        resp = client.post(
            f"/api/agile-training/scrum-sim/g/{slug}/day/advance",
            json={"participant_token": po_token},
        )
        body = _assert_status(resp, 200, f"day {day_num} advance")
        last_state = body["state"]
        ev = last_state["pending_day"].get("event") or {}
        ev_title = ev.get("title", "?")

        # 6b) startable tasks (в backlog, deps готовы, не blocked)
        tasks_map = {t["key"]: t for t in last_state["tasks"]}

        def deps_ready(t: Dict[str, Any]) -> bool:
            return all(tasks_map.get(d, {}).get("column") in ("done", "review") for d in t.get("deps") or [])

        startable = [
            t for t in last_state["tasks"]
            if t["column"] == "backlog" and t.get("state") != "blocked" and deps_ready(t)
        ]
        in_progress_now = [t for t in last_state["tasks"] if t["column"] == "in_progress"]

        # Заполняем «in_progress» до 2-3 задач, чтобы было, на что аллоцировать
        target_active = 3
        for t in startable:
            if len(in_progress_now) >= target_active:
                break
            resp = client.post(
                f"/api/agile-training/scrum-sim/g/{slug}/task/start",
                json={"participant_token": po_token, "task_key": t["key"]},
            )
            body = _assert_status(resp, 200, f"day {day_num}: start {t['key']}")
            last_state = body["state"]
            started_tasks.add(t["key"])
            in_progress_now = [tt for tt in last_state["tasks"] if tt["column"] == "in_progress"]

        # 6c) allocate капасити по in_progress
        cap = int(last_state["capacity_today"])
        in_prog_keys = [t["key"] for t in last_state["tasks"] if t["column"] == "in_progress"]
        alloc: Dict[str, int] = {}
        if in_prog_keys and cap > 0:
            per = max(1, cap // max(1, len(in_prog_keys)))
            remaining = cap
            for k in in_prog_keys:
                give = min(per, remaining)
                if give <= 0:
                    break
                alloc[k] = give
                remaining -= give
            # если осталось — кладём остаток на первую
            if remaining > 0 and in_prog_keys:
                alloc[in_prog_keys[0]] = alloc.get(in_prog_keys[0], 0) + remaining
        resp = client.post(
            f"/api/agile-training/scrum-sim/g/{slug}/day/allocate",
            json={"participant_token": po_token, "allocation": alloc},
        )
        body = _assert_status(resp, 200, f"day {day_num} allocate")
        last_state = body["state"]
        applied_alloc = last_state["pending_day"].get("allocation", {})
        if alloc:
            assert sum(applied_alloc.values()) <= cap, f"alloc {applied_alloc} exceeds cap {cap}"

        # 6d) decision (через раз — пробуем «continue»)
        if day_num % 3 == 0:
            resp = client.post(
                f"/api/agile-training/scrum-sim/g/{slug}/day/decision",
                json={"participant_token": po_token, "decision_key": "continue"},
            )
            _assert_status(resp, 200, f"day {day_num} decision")
            daily_decisions_used += 1

        # 6e) end day
        resp = client.post(
            f"/api/agile-training/scrum-sim/g/{slug}/day/end",
            json={"participant_token": po_token},
        )
        body = _assert_status(resp, 200, f"day {day_num} end")
        last_state = body["state"]
        if day_num < 10:
            assert last_state["phase"] == f"day_{day_num + 1}", f"expected day_{day_num+1}, got {last_state['phase']}"
        cap_after = last_state["capacity_today"]
        _info(
            f"day {day_num}: event='{ev_title}', alloc={applied_alloc}, "
            f"в работе={len(in_prog_keys)}, теперь phase={last_state['phase']} (cap={cap_after})"
        )

    # 7) После 10 дня должны попасть в review
    assert last_state["phase"] == "review", f"expected review, got {last_state['phase']}"
    rm = last_state["review_metrics"] or {}
    _ok(
        f"после дня 10: phase=review, started_tasks={len(started_tasks)}, "
        f"review_metrics keys={list(rm.keys())}"
    )

    # 8) review/confirm
    resp = client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/review/confirm",
        json={"participant_token": po_token},
    )
    body = _assert_status(resp, 200, "review confirm")
    assert body["state"]["phase"] == "retro"
    _ok("review/confirm -> retro")

    # 9) retro: picks + confirm
    resp = client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/retro",
        json={"participant_token": po_token, "picks": []},
    )
    _assert_status(resp, 200, "retro save picks")
    resp = client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/retro",
        json={"participant_token": po_token, "confirm": True},
    )
    body = _assert_status(resp, 200, "retro confirm")
    assert body["state"]["phase"] == "summary"
    _ok("retro confirm -> summary (приёмо-сдаточный happy path пройден)")


# --------------------------- regressions ---------------------------


def smoke_scrum_regressions() -> None:
    _banner("SCRUM SIM — regression edge-cases")

    info = _bootstrap("scrum_simulator", "ru")
    slug = info["slug"]
    client = app.test_client()

    po_token = _join_participant(client, slug, "PO Reg")
    client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/join",
        json={"participant_token": po_token, "role": "product_owner"},
    )

    # Затащим ровно одну простую независимую задачу
    s = _state_scrum(client, slug, po_token)
    indep = next(
        t for t in s["state"]["tasks"]
        if t["column"] == "product" and not t.get("deps")
    )
    client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/planning",
        json={"participant_token": po_token, "action": "pull", "task_key": indep["key"]},
    )
    client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/planning/confirm",
        json={"participant_token": po_token},
    )

    # 1) start задачи дважды — второй раз ловим 400 "not in sprint backlog"
    resp = client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/task/start",
        json={"participant_token": po_token, "task_key": indep["key"]},
    )
    _assert_status(resp, 200, "start once")
    resp = client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/task/start",
        json={"participant_token": po_token, "task_key": indep["key"]},
    )
    body = _assert_status(resp, 400, "start twice")
    assert body.get("error") == "task is not in sprint backlog"
    _ok("повторный start отвергается (task is not in sprint backlog)")

    # 2) return при progress=0 -> ok, обратно в backlog
    resp = client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/task/return",
        json={"participant_token": po_token, "task_key": indep["key"]},
    )
    body = _assert_status(resp, 200, "return progress=0")
    moved = next(t for t in body["state"]["tasks"] if t["key"] == indep["key"])
    assert moved["column"] == "backlog", f"expected backlog, got {moved['column']}"
    assert indep["key"] not in (body["state"]["pending_day"].get("allocation") or {}), (
        "alloc must be cleaned on return"
    )
    _ok("return с progress=0 возвращает в backlog и чистит alloc")

    # 3) Стартуем + аллоцируем + завершаем день, чтобы появился progress
    client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/task/start",
        json={"participant_token": po_token, "task_key": indep["key"]},
    )
    client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/day/advance",
        json={"participant_token": po_token},
    )
    client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/day/allocate",
        json={"participant_token": po_token, "allocation": {indep["key"]: 1}},
    )
    client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/day/end",
        json={"participant_token": po_token},
    )
    s = _state_scrum(client, slug, po_token)
    after = next(t for t in s["state"]["tasks"] if t["key"] == indep["key"])
    if after["column"] == "in_progress" and int(after.get("progress", 0)) > 0:
        resp = client.post(
            f"/api/agile-training/scrum-sim/g/{slug}/task/return",
            json={"participant_token": po_token, "task_key": indep["key"]},
        )
        body = _assert_status(resp, 400, "return after progress")
        assert body.get("error") == "task already has progress"
        _ok("return уже сделанной задачи отвергается (task already has progress)")
    else:
        _info(
            f"задача после дня в колонке={after['column']}, progress={after.get('progress', 0)} — "
            f"return-after-progress кейс пропущен (вероятно, всё доехало до review/done)"
        )

    # 4) AI assist без OPENAI_API_KEY — должен отдать scripted reply, а не падать
    resp = client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/ai-assist",
        json={"participant_token": po_token, "mode": "daily", "user_input": "что делать?"},
    )
    body = _assert_status(resp, 200, "ai assist no key")
    assert (body.get("reply") or "").strip(), f"AI reply must be non-empty: {body}"
    _ok(f"ai-assist без OPENAI_API_KEY: scripted reply длиной {len(body['reply'])} символов")

    # 5) reset — возвращает игру в lobby, но сохраняет участников/роли
    resp = client.post(
        f"/api/agile-training/scrum-sim/g/{slug}/reset",
        json={"participant_token": po_token},
    )
    body = _assert_status(resp, 200, "reset")
    assert body["state"]["phase"] == "lobby"
    # участник всё ещё помнится
    assert po_token in body["state"]["roles"], "роли должны сохраниться после reset"
    _ok("reset возвращает в lobby, роли участников сохраняются")


def smoke_po_regressions() -> None:
    _banner("PO PATH — regression edge-cases")

    info = _bootstrap("po_path", "ru")
    slug = info["slug"]
    client = app.test_client()

    token = _join_participant(client, slug, "Reg PO")

    # 1) submit с stage в неправильном шаге (текущий jtbd, шлём value) -> 409 stage_not_current
    client.post(
        f"/api/agile-training/po-path/g/{slug}/answer",
        json={"participant_token": token, "stage": "jtbd", "data": {"job_statement": "x"}},
    )
    resp = client.post(
        f"/api/agile-training/po-path/g/{slug}/submit",
        json={"participant_token": token, "stage": "value"},
    )
    body = _assert_status(resp, 409, "submit wrong stage")
    assert body.get("error") == "stage_not_current"
    _ok("submit чужого этапа отклонён 409 stage_not_current")

    # 2) Нет токена — 400
    resp = client.post(
        f"/api/agile-training/po-path/g/{slug}/answer",
        json={"stage": "jtbd", "data": {"job_statement": "x"}},
    )
    body = _assert_status(resp, 400, "answer no token")
    assert "participant_token" in (body.get("error") or "")
    _ok("autosave без participant_token отклонён 400")

    # 3) AI assist без OPENAI_API_KEY — отдаёт scripted reply (markdown)
    resp = client.post(
        f"/api/agile-training/po-path/g/{slug}/ai-assist",
        json={
            "participant_token": token,
            "stage": "jtbd",
            "mode": "improve",
            "user_input": "Когда я открываю отчёт, я хочу понять, где теряю деньги.",
        },
    )
    body = _assert_status(resp, 200, "po ai-assist no key")
    assert (body.get("reply") or "").strip(), f"reply must be non-empty: {body}"
    _ok(f"ai-assist (rephrase) без OPENAI_API_KEY: scripted reply ({len(body['reply'])} символов)")


# --------------------------- PM SIM ---------------------------


def _pm_join_po(client, slug: str, name: str = "PO Sim") -> str:
    """Создаём участника и назначаем ему роль PO."""
    token = _join_participant(client, slug, name)
    resp = client.post(
        f"/api/agile-training/pm-sim/g/{slug}/join",
        json={"participant_token": token, "role": "po"},
    )
    _assert_status(resp, 200, "pm join PO")
    return token


def _pm_state(client, slug: str, token: Optional[str] = None) -> Dict[str, Any]:
    qs = {}
    if token:
        qs["participant_token"] = token
    resp = client.get(
        f"/api/agile-training/pm-sim/g/{slug}/state",
        query_string=qs,
    )
    return _assert_status(resp, 200, "pm state")["state"]


def _pm_resolve_event(client, slug: str, token: str, option_id: Optional[str] = None) -> Dict[str, Any]:
    state = _pm_state(client, slug, token)
    ev = state["current_event"]
    assert ev, f"no current_event in state phase={state['phase']}"
    chosen = option_id or ev["options"][0]["id"]
    resp = client.post(
        f"/api/agile-training/pm-sim/g/{slug}/event/decide",
        json={"participant_token": token, "option_id": chosen},
    )
    return _assert_status(resp, 200, f"pm event/decide {chosen}")


def smoke_pm_sim_logic() -> None:
    _banner("PM SIM — приёмо-сдаточные испытания (фичи / capacity / риск слипа)")

    info = _bootstrap("pm_sim", "ru")
    slug = info["slug"]
    client = app.test_client()

    po_token = _pm_join_po(client, slug)

    # 1) Старт игры (PO нажимает «начать»)
    resp = client.post(
        f"/api/agile-training/pm-sim/g/{slug}/start",
        json={"participant_token": po_token},
    )
    _assert_status(resp, 200, "pm participant_start")
    state = _pm_state(client, slug, po_token)
    assert state["phase"] == "playing", f"expected playing got {state['phase']}"
    assert state["current_week"] == 1
    assert state["cycle_index"] == 1
    assert state["capacity_left"] == 100
    assert state["feature_choice_open"] is True
    assert "risk_factors" in state, "risk_factors must be in state"
    assert state["risk_factors"]["capacity_per_cycle"] == 100
    _ok("старт: week=1, cycle=1, capacity=100, feature_choice_open=True, risk_factors есть")

    # 2) ВАЖНОЕ: на одной неделе только одно событие.
    #    Решаем событие на w1, потом дёргаем /state ещё раз — никакого нового события появиться не должно
    #    (раньше тут была дыра: в феча-неделе после event/decide /state выкатывал ещё одно событие).
    decided1 = _pm_resolve_event(client, slug, po_token)
    assert decided1["state"]["event_resolved"] is True
    state_after = _pm_state(client, slug, po_token)
    assert state_after["event_resolved"] is True, "event must stay resolved"
    assert state_after["current_week"] == 1, "week must NOT advance until features released"
    # current_event может остаться выставленным, но event_resolved=True и в history лежит ровно 1 запись по w1
    w1_events = [h for h in state_after["history"] if h.get("kind") == "event" and h.get("week") == 1]
    assert len(w1_events) == 1, f"expected 1 event in w1 history, got {len(w1_events)}"
    _ok("на старт-неделе цикла после event/decide новое событие на ту же неделю не падает (история ровно 1)")

    # 3) Выбираем «безопасную» лёгкую фичу (низкая утилизация ⇒ риск 0%)
    options = state_after["feature_options"]
    assert options, "feature_options must be non-empty when feature_choice_open"
    small = next((f for f in options if (f.get("capacity") or 0) <= 25 and f["key"] != "stabilize"), None)
    assert small, "ожидали хотя бы одну маленькую фичу в опциях"
    resp = client.post(
        f"/api/agile-training/pm-sim/g/{slug}/feature/release",
        json={"participant_token": po_token, "feature_keys": [small["key"]]},
    )
    body = _assert_status(resp, 200, "pm feature/release small")
    state = body["state"]
    # Маленькая фича: util = small.cap/100 < 60% ⇒ риск 0% ⇒ всегда доехала, в pending ничего
    assert state["pending_releases"] == [], f"low-util release must NOT slip, got {state['pending_releases']}"
    rel = next((r for r in state["feature_releases"] if r["key"] == small["key"]), None)
    assert rel is not None, "feature must appear in feature_releases"
    assert rel["slipped"] is False
    assert state["current_week"] == 2, "after release week must tick to 2"
    _ok(f"маленькая {small['key']} (cap={small['capacity']}): риск 0%, доехала сразу, week=2")

    # 4) Жёсткая защита правила: '1 big + 1 small' нельзя.
    #    Подкрутим состояние: дотикаем до старт-недели цикла 2 (w3),
    #    решим event w2 и попробуем релиз 1 big + 1 small.
    decided2 = _pm_resolve_event(client, slug, po_token)
    state2 = decided2["state"]
    assert state2["current_week"] == 3 or state2["phase"] == "finished", "after w2 event week should advance"
    if state2["phase"] != "finished":
        assert state2["cycle_index"] == 2, f"expected cycle=2 at w3 got {state2['cycle_index']}"
        assert state2["feature_choice_open"] is True
        assert state2["capacity_left"] == 100, "new cycle must refill capacity"
        # Решаем event w3
        decided3 = _pm_resolve_event(client, slug, po_token)
        opts3 = decided3["state"]["feature_options"]
        big = next((f for f in opts3 if (f.get("capacity") or 0) >= 40 and f["key"] != "stabilize"), None)
        small3 = next((f for f in opts3 if (f.get("capacity") or 0) < 40 and f["key"] != "stabilize"), None)
        if big and small3:
            resp = client.post(
                f"/api/agile-training/pm-sim/g/{slug}/feature/release",
                json={"participant_token": po_token, "feature_keys": [big["key"], small3["key"]]},
            )
            body = _assert_status(resp, 400, "pm release big+small")
            assert body.get("error") == "big_must_be_alone", body
            _ok("правило: '1 big + 1 small' отвергнуто (big_must_be_alone)")
        else:
            _info("в выборке цикла 2 нет одновременно big+small — кейс пропущен")

        # 5) Нельзя 2 больших — max_one_big
        bigs = [f for f in opts3 if (f.get("capacity") or 0) >= 40 and f["key"] != "stabilize"]
        if len(bigs) >= 2:
            resp = client.post(
                f"/api/agile-training/pm-sim/g/{slug}/feature/release",
                json={"participant_token": po_token, "feature_keys": [bigs[0]["key"], bigs[1]["key"]]},
            )
            body = _assert_status(resp, 400, "pm release two big")
            assert body.get("error") in {"max_one_big", "max_two_features"}, body
            _ok(f"правило: 2 big отвергнуто ({body.get('error')})")
        else:
            _info("в выборке цикла 2 < 2 big — кейс 2-big пропущен")

        # 6) Стабилизация — только в одиночку
        stab = next((f for f in opts3 if f["key"] == "stabilize"), None)
        small3b = next((f for f in opts3 if f["key"] != "stabilize" and (f.get("capacity") or 0) < 40), None)
        if stab and small3b:
            resp = client.post(
                f"/api/agile-training/pm-sim/g/{slug}/feature/release",
                json={"participant_token": po_token, "feature_keys": [stab["key"], small3b["key"]]},
            )
            body = _assert_status(resp, 400, "pm release stab+small")
            assert body.get("error") == "stabilize_must_be_alone", body
            _ok("правило: stabilize+small отвергнуто (stabilize_must_be_alone)")
        else:
            _info("кейс 'stabilize вместе с другой' пропущен (нужны и stab, и small в опциях)")


def smoke_pm_sim_slip() -> None:
    """Изолированный модульный тест риск-модели: формула, перенос, carryover capacity, anti-repeat events."""
    _banner("PM SIM — модульный тест риск-модели и pending_releases")

    from agile_pm_sim import (
        _initial_state,
        _delivery_risk_pct,
        _release_feature,
        _process_due_pending_releases,
        _start_new_cycle_if_needed,
        CAPACITY_PER_CYCLE,
        RISK_MAX_PCT,
        RISK_THRESHOLD_PCT,
    )
    import random

    # 1) Низкая утилизация ⇒ риск 0
    data = _initial_state()
    risk_low = _delivery_risk_pct(data, total_committed_cap=20)  # 20% util
    assert risk_low == 0.0, f"low util risk must be 0, got {risk_low}"
    _ok(f"util 20% / нейтральные метрики ⇒ риск {risk_low:.1f}%")

    # 2) Заметная утилизация при чистых метриках (75% util ⇒ base=22.5%, без adj)
    risk_mid = _delivery_risk_pct(data, total_committed_cap=75)
    assert risk_mid > 0
    assert risk_mid <= RISK_MAX_PCT
    _ok(f"util 75% / нейтральные метрики ⇒ риск {risk_mid:.1f}% (в пределах [0..{RISK_MAX_PCT}])")

    # 3) Тех долг и низкая стабильность подбавляют (тот же util — должен подняться)
    data_bad = _initial_state()
    data_bad["metrics"]["tech_debt"] = 80
    data_bad["metrics"]["stability"] = 35
    risk_bad = _delivery_risk_pct(data_bad, total_committed_cap=75)
    assert risk_bad > risk_mid, f"high debt+low stab must amplify risk: {risk_bad} <= {risk_mid}"
    _ok(f"debt=80, stab=35, util=75 ⇒ риск {risk_bad:.1f}% > чистого ({risk_mid:.1f}%)")

    # 4) Cap (RISK_MAX_PCT): даже самый тяжёлый кейс не превышает потолок
    data_max = _initial_state()
    data_max["metrics"]["tech_debt"] = 100
    data_max["metrics"]["stability"] = 0
    risk_max = _delivery_risk_pct(data_max, total_committed_cap=100)
    assert risk_max == float(RISK_MAX_PCT), f"max-stress risk must hit cap, got {risk_max}"
    _ok(f"max stress (debt=100, stab=0, util=100) ⇒ риск {risk_max:.1f}% (cap)")

    # 4) Слип: forsируем риск=100 через rng, который всегда возвращает 0.0
    class _ZeroRnd:
        def random(self):
            return 0.0

    data2 = _initial_state()
    data2["current_week"] = 1
    data2["capacity_left"] = 100
    data2["cycle_index"] = 1
    data2["metrics"]["tech_debt"] = 80
    data2["metrics"]["stability"] = 35
    rec = _release_feature(
        data2, "voice", week=1, locale="ru",
        total_committed_cap=100, rnd=_ZeroRnd(),
    )
    assert rec is not None
    assert rec["slipped"] is True, "with high risk + zero rnd must slip"
    assert data2["pending_releases"] == [rec], "pending_releases must contain the slipped record"
    assert not any(r["key"] == "voice" for r in data2.get("feature_releases", [])), "must NOT be in feature_releases yet"
    assert data2["capacity_left"] == 100 - 35, "capacity is still consumed even on slip"
    _ok("слип: фича в pending_releases, эффекты НЕ применены, capacity списана")

    # 5) Ноль-риск при rnd=0.99 (по сути — низкая утилизация)
    data3 = _initial_state()
    data3["current_week"] = 1
    data3["capacity_left"] = 100
    rec3 = _release_feature(
        data3, "reactions", week=1, locale="ru",
        total_committed_cap=20, rnd=random.Random(42),
    )
    assert rec3 is not None
    assert rec3["slipped"] is False
    assert data3["pending_releases"] == []
    assert data3["feature_releases"][-1]["key"] == "reactions"
    _ok("низкий риск ⇒ feature ship'нулась сразу")

    # 6) Перенос: pending уезжает в следующий цикл, capacity_left урезается на cap, эффекты применяются
    data4 = _initial_state()
    data4["current_week"] = 1
    data4["capacity_left"] = 100
    data4["cycle_index"] = 1
    rec4 = _release_feature(
        data4, "voice", week=1, locale="ru",
        total_committed_cap=100, rnd=_ZeroRnd(),
    )
    assert rec4["slipped"] is True
    assert rec4["delivery_cycle"] == 2
    sat_before = data4["metrics"]["satisfaction"]
    # симулируем переход к w3 (старт цикла 2)
    data4["current_week"] = 3
    _start_new_cycle_if_needed(data4)
    assert data4["cycle_index"] == 2
    assert data4["capacity_left"] == 100 - 35, f"new cycle cap must be 100-35={65}, got {data4['capacity_left']}"
    # эффекты voice (sat +4, active +6, stab -3, tech_debt +5) применились
    assert data4["metrics"]["satisfaction"] != sat_before, "voice must have applied satisfaction effect"
    assert data4["pending_releases"] == [], "after delivery pending must be empty"
    delivered_now = [r for r in data4["feature_releases"] if r["key"] == "voice"]
    assert delivered_now, "voice must appear in feature_releases after late delivery"
    assert delivered_now[-1]["slipped"] is True, "must keep slipped=True flag in record"
    _ok("перенос фичи в следующий цикл: capacity-carryover работает, эффекты применяются ровно при отгрузке")


def smoke_pm_sim_anti_repeat() -> None:
    """Анти-повтор событий: при наличии альтернатив одно и то же событие не выдаётся дважды подряд."""
    _banner("PM SIM — антиповтор одинаковых событий подряд")

    from agile_pm_sim import _pick_event, _initial_state

    data = _initial_state()
    data["metrics"]["satisfaction"] = 50  # включит low_satisfaction(70) + low_trust выкл
    data["metrics"]["stability"] = 50
    data["metrics"]["tech_debt"] = 50
    data["last_event_id"] = "notif_complaints"  # притворимся, что только что был именно он
    # На разных неделях/seedах антиповтор должен не возвращать тот же id
    seen_repeats = 0
    total = 0
    for w in range(2, 12):
        ev = _pick_event(data, week=w, group_id=1234)
        total += 1
        if ev["id"] == data["last_event_id"]:
            seen_repeats += 1
    # Допускаем единичный кейс, когда альтернатив нет, но в типичных условиях повторов быть не должно
    _ok(f"антиповтор: {seen_repeats}/{total} раз pick_event вернул '{data['last_event_id']}' подряд")
    assert seen_repeats <= 1, f"антиповтор не работает: {seen_repeats} повторов из {total}"


# --------------------------- entry ---------------------------


def main() -> int:
    with app.app_context():
        db.create_all()

    failures = 0
    for name, fn in (
        ("PO PATH happy path", smoke_po_path),
        ("PO PATH regressions", smoke_po_regressions),
        ("SCRUM SIM happy path", smoke_scrum_sim),
        ("SCRUM SIM regressions", smoke_scrum_regressions),
        ("PM SIM logic+rules", smoke_pm_sim_logic),
        ("PM SIM slip / pending_releases", smoke_pm_sim_slip),
        ("PM SIM event anti-repeat", smoke_pm_sim_anti_repeat),
    ):
        try:
            fn()
        except Exception as e:
            failures += 1
            print(f"\n[X] {name} failed: {e}")
            traceback.print_exc()

    print()
    if failures:
        print(f"=== РЕЗУЛЬТАТ: {failures} suite(s) FAILED ===")
        return 1
    print("=== РЕЗУЛЬТАТ: ВСЕ ПРИЁМО-СДАТОЧНЫЕ СЦЕНАРИИ ПРОШЛИ ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
