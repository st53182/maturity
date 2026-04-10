import json
from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import Question, Assessment, Team
from flask import current_app
from datetime import datetime



bp_survey = Blueprint('survey', __name__)


def _normalize_survey_lang(lang):
    if not lang:
        return 'ru'
    l = str(lang).lower().strip()
    return 'en' if l.startswith('en') else 'ru'


def _result_display_keys(category, subcategory, category_en, subcategory_en, lang):
    if lang == 'en' and category_en and subcategory_en:
        ce = str(category_en).strip()
        se = str(subcategory_en).strip()
        if ce and se:
            return ce, se
    return category, subcategory


def _question_display_keys(question, lang):
    return _result_display_keys(
        question.category,
        question.subcategory,
        getattr(question, 'category_en', None),
        getattr(question, 'subcategory_en', None),
        lang,
    )


# 🔹 Создание команды
@bp_survey.route('/create_team', methods=['POST'])
@jwt_required()
def create_team():
    try:
        print(f"📥 Запрос на создание команды: {request.json}")  # 🔹 Лог запроса

        data = request.get_json()
        if not data:
            return jsonify({"error": "Необходимо передать JSON"}), 400

        user_id = get_jwt_identity()
        team_name = data.get("team_name")

        if not team_name:
            return jsonify({"error": "Название команды обязательно"}), 400

        # Проверяем, нет ли уже команды с таким названием у пользователя
        existing_team = Team.query.filter_by(name=team_name, user_id=user_id).first()
        if existing_team:
            return jsonify({"error": "Команда с таким названием уже существует"}), 409  # 409 - Conflict

        # 🔹 Создаём команду с датой создания
        new_team = Team(name=team_name, user_id=user_id, created_at=datetime.utcnow())

        db.session.add(new_team)
        db.session.commit()

        print(f"✅ Команда '{team_name}' создана! ID: {new_team.id}")

        return jsonify({"message": "Команда создана!", "team_id": new_team.id}), 201

    except Exception as e:
        print(f"🔥 Ошибка создания команды: {e}")
        return jsonify({"error": "Ошибка сервера", "details": str(e)}), 500


# 🔹 Получение всех вопросов
@bp_survey.route('/questions', methods=['GET'])
def get_questions():
    try:
        lang = request.args.get('lang', 'ru')
        questions = Question.query.all()

        response = [{
            "id": q.id,
            "category": q.category_en if lang == 'en' and q.category_en else q.category,
            "subcategory": q.subcategory_en if lang == 'en' and q.subcategory_en else q.subcategory,
            "question": q.question_en if lang == 'en' and q.question_en else q.question,
            "levels": {
                "basic": q.level_basic_en if lang == 'en' and q.level_basic_en else q.level_basic,
                "transitional": q.level_transitional_en if lang == 'en' and q.level_transitional_en else q.level_transitional,
                "growing": q.level_growing_en if lang == 'en' and q.level_growing_en else q.level_growing,
                "normalization": q.level_normalization_en if lang == 'en' and q.level_normalization_en else q.level_normalization,
                "optimal": q.level_optimal_en if lang == 'en' and q.level_optimal_en else q.level_optimal,
            }
        } for q in questions]

        return current_app.response_class(
            response=json.dumps(response, ensure_ascii=False),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        error_msg = "Error getting questions" if request.args.get('lang') == 'en' else "Ошибка при получении вопросов"
        return jsonify({"error": error_msg, "details": str(e)}), 500

SCORE_MAP = {
    "basic": 1,
    "transitional": 2,
    "growing": 3,
    "normalization": 4,
    "optimal": 5
}
# 🔹 Сохранение оценок команды
@bp_survey.route('/submit_assessment', methods=['POST'])
@jwt_required()
def submit_assessment():
    data = request.json
    user_id = get_jwt_identity()
    team_id = data.get("team_id")
    answers = data.get("answers")

    if not team_id or not answers:
        return jsonify({"error": "Необходимо указать команду и ответы"}), 400

    last_assessment_id = None

    for q_id, score in answers.items():
        numeric_score = SCORE_MAP.get(score)  # ✅ Конвертируем строку в число
        if numeric_score is None:
            return jsonify({"error": f"Некорректное значение оценки: {score}"}), 400

        assessment = Assessment(
            user_id=user_id,
            team_id=team_id,
            question_id=q_id,
            score=numeric_score
        )
        db.session.add(assessment)
        db.session.flush()  # 👈 Позволяет получить ID до коммита
        last_assessment_id = assessment.id

    db.session.commit()

    return jsonify({
        "message": "Результаты сохранены!",
        "assessment_id": last_assessment_id  # 👈 Возвращаем ID
    })


# 🔹 Получение истории оценок
@bp_survey.route('/team_progress/<int:team_id>', methods=['GET'])
@jwt_required()
def get_team_progress(team_id):
    assessments = (
        db.session.query(
            Question.category,
            Question.question,
            db.func.avg(Assessment.score).label("average_score")
        )
        .join(Assessment, Question.id == Assessment.question_id)
        .filter(Assessment.team_id == team_id)
        .group_by(Question.category, Question.question)
        .all()
    )

    result = []
    for category, question, avg_score in assessments:
        result.append({
            "category": category,
            "question": question,
            "average_score": float(avg_score)
        })

    return jsonify(result)


@bp_survey.route('/user_teams', methods=['GET'])
@jwt_required()
def get_user_teams():
    user_id = get_jwt_identity()
    teams = Team.query.filter_by(user_id=user_id).all()

    team_data = []

    for team in teams:
        # Получаем последний assessment по дате
        latest_assessment = (
            Assessment.query
            .filter_by(team_id=team.id, user_id=user_id)
            .order_by(Assessment.created_at.desc())
            .first()
        )

        team_data.append({
            "id": team.id,
            "name": team.name,
            "latest_assessment_id": latest_assessment.id if latest_assessment else None
        })

    return jsonify(team_data)
@bp_survey.route("/assessment/<int:assessment_id>/recommendations", methods=["GET"])
@jwt_required()
def get_recommendations(assessment_id):
    assessment = Assessment.query.get(assessment_id)
    if assessment and assessment.recommendations:
        return jsonify({"recommendations": assessment.recommendations})
    return jsonify({"recommendations": None}), 200

@bp_survey.route('/team_average/<int:team_id>', methods=['GET'])
@jwt_required()
def get_team_average(team_id):
    try:
        # Вычисляем среднее значение оценки для заданной команды
        avg_score = db.session.query(db.func.avg(Assessment.score)) \
                              .filter(Assessment.team_id == team_id) \
                              .scalar()
        if avg_score is None:
            return jsonify({"error": "Нет данных для команды."}), 404

        # Округляем результат до 2 знаков после запятой
        return jsonify({"average_score": round(avg_score, 2)})
    except Exception as e:
        return jsonify({"error": "Ошибка при получении средней оценки", "details": str(e)}), 500

@bp_survey.route('/team_results/<int:team_id>', methods=['GET'])
@jwt_required()
def get_team_results(team_id):
    try:
        lang = _normalize_survey_lang(request.args.get('lang'))
        # Загружаем команду
        team = Team.query.get(team_id)
        if not team:
            return jsonify({"error": "Команда не найдена"}), 404

        # Загружаем оценки команды
        assessments = db.session.query(
            Question.category,
            Question.subcategory,
            Question.category_en,
            Question.subcategory_en,
            db.func.avg(Assessment.score).label("average_score")
        ).join(Assessment, Question.id == Assessment.question_id) \
            .filter(Assessment.team_id == team_id) \
            .group_by(
                Question.category,
                Question.subcategory,
                Question.category_en,
                Question.subcategory_en,
                Assessment.created_at,
            ) \
            .order_by(Assessment.created_at.desc()) \
            .limit(35) \
            .all()

        # Формируем структуру данных
        results = {}
        for category, subcategory, category_en, subcategory_en, avg_score in assessments:
            ckey, skey = _result_display_keys(
                category, subcategory, category_en, subcategory_en, lang
            )
            if ckey not in results:
                results[ckey] = {}
            results[ckey][skey] = round(avg_score, 2)

        # Возвращаем имя команды и результаты
        return jsonify({
            "team_name": team.name,
            "results": results
        })
    except Exception as e:
        return jsonify({"error": "Ошибка при получении результатов", "details": str(e)}), 500


@bp_survey.route('/temp_results', methods=['POST'])
def save_temp_results():
    """
    Saves the survey results temporarily for unauthenticated users.
    """
    data = request.json
    answers = data.get("answers")

    if not answers:
        return jsonify({"error": "No answers provided"}), 400

    # Store answers in the session (temporary storage)
    session['temp_results'] = answers

    return jsonify({"message": "Results saved temporarily", "temp_id": "guest"}), 200


@bp_survey.route('/temp_results', methods=['GET'])
def get_temp_results():
    """
    Retrieves temporary survey results for unauthenticated users.
    """
    temp_results = session.get('temp_results')
    if not temp_results:
        return jsonify({"error": "No temporary results found"}), 404

    return jsonify(temp_results), 200

@bp_survey.route("/assessment/<int:assessment_id>/recommendations", methods=["POST"])
@jwt_required()
def save_recommendations(assessment_id):
    data = request.json
    recommendations = data.get("recommendations")

    if not recommendations:
        return jsonify({"error": "Нет текста рекомендаций"}), 400

    assessment = Assessment.query.get(assessment_id)
    if not assessment:
        return jsonify({"error": "Оценка не найдена"}), 404

    assessment.recommendations = recommendations
    db.session.commit()

    return jsonify({"message": "Рекомендации сохранены"}), 200


@bp_survey.route('/team_results_history/<int:team_id>', methods=['GET'])
@jwt_required()
def get_team_results_history(team_id):
    user_id = get_jwt_identity()
    lang = _normalize_survey_lang(request.args.get('lang'))

    # Загружаем все оценки команды (самые новые сверху)
    assessments = (
        db.session.query(Assessment)
        .filter_by(team_id=team_id, user_id=user_id)
        .order_by(Assessment.created_at.desc())
        .all()
    )

    # Группируем по дате (с точностью до секунды)
    sessions = {}
    for a in assessments:
        session_key = a.created_at.strftime('%Y-%m-%d %H:%M:%S')
        if session_key not in sessions:
            sessions[session_key] = []
        sessions[session_key].append(a)

    # Берём 2 последние сессии
    latest_sessions = dict(sorted(sessions.items(), reverse=True)[:2])

    history = {}

    for session_key, records in latest_sessions.items():
        temp_result = {}
        for a in records:
            category, subcategory = _question_display_keys(a.question, lang)
            if category not in temp_result:
                temp_result[category] = {}
            if subcategory not in temp_result[category]:
                temp_result[category][subcategory] = []
            temp_result[category][subcategory].append(a.score)

        # Считаем среднее значение для каждой подкатегории
        averaged = {}
        for category, subs in temp_result.items():
            averaged[category] = {
                sub: round(sum(scores) / len(scores), 2)
                for sub, scores in subs.items()
            }
        history[session_key] = averaged

    return jsonify(history)
