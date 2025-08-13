from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import Survey, SurveyResponse, SurveyInvitation, Team, Employee, User
import uuid
from datetime import datetime
import json

surveys_bp = Blueprint('surveys', __name__)

ENPS_TEMPLATE = [
    {"id": 1, "type": "radio", "question": "Укажите ваш формат работы:", "options": ["Офисный", "Удаленный", "Гибридный"], "required": True},
    {"id": 2, "type": "textarea", "question": "Какие шаги, по вашему мнению, компания могла бы предпринять для улучшения вашего опыта работы?", "required": False},
    {"id": 3, "type": "scale", "question": "Насколько вы удовлетворены своим опытом работы в компании?", "scale": [1,2,3,4,5], "required": True},
    {"id": 4, "type": "textarea", "question": "Какие меры, на ваш взгляд, компания могла бы принять, чтобы вы охотнее рекомендовали ее своим друзьям как место для работы?", "required": False},
    {"id": 5, "type": "scale", "question": "Порекомендовали бы вы работать здесь своим друзьям?", "scale": [1,2,3,4,5], "required": True},
    {"id": 6, "type": "scale", "question": "Чувствуете ли вы, что у вас есть возможность расти в этой компании?", "scale": [1,2,3,4,5], "required": True},
    {"id": 7, "type": "textarea", "question": "Какие изменения, по вашему мнению, руководство могло бы внести для улучшения качества рабочих условий сотрудников?", "required": True},
    {"id": 8, "type": "scale", "question": "Считаете ли вы, что у вас есть все ресурсы и инструменты, необходимые для выполнения вашей работы эффективно?", "scale": [1,2,3,4,5], "required": True},
    {"id": 9, "type": "scale", "question": "В какой степени вы чувствуете, что растете внутри компании как эксперт в своей области?", "scale": [1,2,3,4,5], "required": True}
]

FEEDBACK_360_TEMPLATE = [
    {"id": 1, "type": "text", "question": "Имя", "required": True},
    {"id": 2, "type": "textarea", "question": "В чем заключаются ключевые личные, профессиональные и лидерские (если применимо) таланты сотрудника?", "required": False},
    {"id": 3, "type": "textarea", "question": "Каковы области личного, профессионального и лидерского (если применимо) совершенствования и развития сотрудника?", "required": False},
    {"id": 4, "type": "textarea", "question": "На основе ваших наблюдений приведите примеры того, как сотрудник развивается личностно, профессионально и как лидер (если применимо).", "required": False},
    {"id": 5, "type": "textarea", "question": "Другие комментарии", "required": False},
    {"id": 6, "type": "matrix", "question": "Оцените", "required": True, "rows": [
        "Межличностные: Предоставление обратной связи",
        "Межличностные: Лидерство (если применимо)", 
        "Социальное: Эффективное общение",
        "Решение проблем: Достижение результатов",
        "Решение проблем: Движущая сила инноваций",
        "Социальное: Сотрудничество (отношение к командной работе)",
        "Профессионал: Ответственность и подотчетность",
        "Профессионал: Профессиональная компетентность",
        "Профессионал: Продуктивность и организация труда",
        "Межличностные: Взаимное уважение"
    ], "scale": ["Требует срочной корректировки", "Требует улучшения", "Соответствует занимаемой должности", "Превосходит ожидания", "Выдающийся результат"]}
]

@surveys_bp.route('/surveys', methods=['GET'])
@jwt_required()
def get_surveys():
    user_id = get_jwt_identity()
    surveys = Survey.query.filter_by(creator_id=user_id).all()
    
    result = []
    for survey in surveys:
        response_count = len(survey.responses)
        result.append({
            'id': survey.id,
            'title': survey.title,
            'survey_type': survey.survey_type,
            'status': survey.status,
            'response_count': response_count,
            'created_at': survey.created_at.isoformat(),
            'deadline': survey.deadline.isoformat() if survey.deadline else None,
            'access_token': survey.access_token
        })
    
    return jsonify(result)

@surveys_bp.route('/surveys', methods=['POST'])
@jwt_required()
def create_survey():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    survey_type = data.get('survey_type')
    title = data.get('title')
    team_id = data.get('team_id')
    target_employee_id = data.get('target_employee_id')
    
    if survey_type == 'enps':
        questions = ENPS_TEMPLATE
    elif survey_type == '360':
        questions = FEEDBACK_360_TEMPLATE
    else:
        return jsonify({'error': 'Invalid survey type'}), 400
    
    if 'questions' in data:
        questions = data['questions']
    
    survey = Survey(
        title=title,
        survey_type=survey_type,
        creator_id=user_id,
        team_id=team_id,
        target_employee_id=target_employee_id,
        access_token=str(uuid.uuid4()),
        questions=questions,
        settings=data.get('settings', {}),
        deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None
    )
    
    db.session.add(survey)
    db.session.commit()
    
    return jsonify({
        'id': survey.id,
        'access_token': survey.access_token,
        'public_url': f'/survey/{survey.access_token}'
    }), 201

@surveys_bp.route('/surveys/<int:survey_id>/send', methods=['POST'])
@jwt_required()
def send_survey_invitations(survey_id):
    user_id = get_jwt_identity()
    survey = Survey.query.filter_by(id=survey_id, creator_id=user_id).first()
    
    if not survey:
        return jsonify({'error': 'Survey not found'}), 404
    
    data = request.get_json()
    emails = data.get('emails', [])
    
    invitations = []
    for email in emails:
        invitation = SurveyInvitation(
            survey_id=survey.id,
            email=email,
            access_token=str(uuid.uuid4())
        )
        db.session.add(invitation)
        invitations.append(invitation)
    
    survey.status = 'active'
    db.session.commit()
    
    links = [f'/survey/{inv.access_token}' for inv in invitations]
    
    return jsonify({
        'message': f'Survey sent to {len(emails)} recipients',
        'links': links
    })

@surveys_bp.route('/survey/<access_token>', methods=['GET'])
def get_survey_by_token(access_token):
    survey = Survey.query.filter_by(access_token=access_token).first()
    invitation = None
    
    if not survey:
        invitation = SurveyInvitation.query.filter_by(access_token=access_token).first()
        if invitation:
            survey = invitation.survey
    
    if not survey:
        return jsonify({'error': 'Survey not found'}), 404
    
    if survey.status != 'active':
        return jsonify({'error': 'Survey is not active'}), 400
    
    if invitation and invitation.responded_at:
        return jsonify({'error': 'You have already responded to this survey'}), 400
    
    return jsonify({
        'id': survey.id,
        'title': survey.title,
        'survey_type': survey.survey_type,
        'questions': survey.questions,
        'deadline': survey.deadline.isoformat() if survey.deadline else None,
        'access_token': access_token
    })

@surveys_bp.route('/survey/<access_token>/submit', methods=['POST'])
def submit_survey_response(access_token):
    survey = Survey.query.filter_by(access_token=access_token).first()
    invitation = None
    
    if not survey:
        invitation = SurveyInvitation.query.filter_by(access_token=access_token).first()
        if invitation:
            survey = invitation.survey
    
    if not survey:
        return jsonify({'error': 'Survey not found'}), 404
    
    if survey.status != 'active':
        return jsonify({'error': 'Survey is not active'}), 400
    
    data = request.get_json()
    answers = data.get('answers')
    respondent_name = data.get('respondent_name')
    
    response = SurveyResponse(
        survey_id=survey.id,
        respondent_email=invitation.email if invitation else None,
        respondent_name=respondent_name,
        answers=answers,
        ip_address=request.remote_addr
    )
    
    db.session.add(response)
    
    if invitation:
        invitation.responded_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': 'Response submitted successfully'})

@surveys_bp.route('/surveys/<int:survey_id>/results', methods=['GET'])
@jwt_required()
def get_survey_results(survey_id):
    user_id = get_jwt_identity()
    survey = Survey.query.filter_by(id=survey_id, creator_id=user_id).first()
    
    if not survey:
        return jsonify({'error': 'Survey not found'}), 404
    
    responses = survey.responses
    
    if survey.survey_type == 'enps':
        analytics = analyze_enps_results(responses)
    else:
        analytics = analyze_360_results(responses, show_names=(user_id == survey.creator_id))
    
    return jsonify({
        'survey': {
            'id': survey.id,
            'title': survey.title,
            'survey_type': survey.survey_type,
            'response_count': len(responses)
        },
        'analytics': analytics,
        'responses': [r.answers for r in responses] if survey.survey_type == 'enps' else None
    })

@surveys_bp.route('/employees', methods=['GET'])
@jwt_required()
def get_employees():
    user_id = get_jwt_identity()
    employees = Employee.query.filter_by(user_id=user_id).all()
    
    result = []
    for employee in employees:
        result.append({
            'id': employee.id,
            'name': employee.name,
            'role': employee.role
        })
    
    return jsonify(result)

def analyze_enps_results(responses):
    if not responses:
        return {}
    
    scale_questions = [3, 5, 6, 8, 9]
    averages = {}
    
    for q_id in scale_questions:
        scores = []
        for response in responses:
            if str(q_id) in response.answers:
                scores.append(int(response.answers[str(q_id)]))
        
        if scores:
            averages[f'question_{q_id}'] = {
                'average': sum(scores) / len(scores),
                'count': len(scores),
                'distribution': {str(i): scores.count(i) for i in range(1, 6)}
            }
    
    return {
        'response_count': len(responses),
        'averages': averages,
        'nps_score': calculate_nps_score([r.answers.get('5') for r in responses if r.answers.get('5')])
    }

def analyze_360_results(responses, show_names=False):
    if not responses:
        return {}
    
    matrix_data = {}
    for response in responses:
        matrix_answers = response.answers.get('6', {})
        for row, rating in matrix_answers.items():
            if row not in matrix_data:
                matrix_data[row] = []
            matrix_data[row].append(rating)
    
    competency_averages = {}
    for competency, ratings in matrix_data.items():
        if ratings:
            numeric_ratings = [convert_rating_to_number(r) for r in ratings]
            competency_averages[competency] = {
                'average': sum(numeric_ratings) / len(numeric_ratings),
                'count': len(numeric_ratings)
            }
    
    result = {
        'response_count': len(responses),
        'competency_averages': competency_averages
    }
    
    if show_names:
        result['detailed_responses'] = [
            {
                'respondent_name': r.respondent_name,
                'answers': r.answers,
                'submitted_at': r.submitted_at.isoformat()
            } for r in responses
        ]
    
    return result

def calculate_nps_score(scores):
    if not scores:
        return 0
    
    numeric_scores = [int(s) for s in scores if s is not None]
    if not numeric_scores:
        return 0
    
    promoters = len([s for s in numeric_scores if s >= 4])
    detractors = len([s for s in numeric_scores if s <= 2])
    total = len(numeric_scores)
    
    return ((promoters - detractors) / total) * 100 if total > 0 else 0

def convert_rating_to_number(rating_text):
    rating_map = {
        "Требует срочной корректировки": 1,
        "Требует улучшения": 2, 
        "Соответствует занимаемой должности": 3,
        "Превосходит ожидания": 4,
        "Выдающийся результат": 5
    }
    return rating_map.get(rating_text, 3)
