from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import User, DISCAssessment
import openai
import os
import logging

disc_bp = Blueprint('disc_assessment', __name__)

DISC_QUESTIONS = [
    {
        "id": 1,
        "question": "Как менеджер, я предпочитаю принимать решения:",
        "options": [
            {"text": "Быстро и решительно, основываясь на своей интуиции", "type": "D", "score": 3},
            {"text": "После обсуждения с командой и получения их мнений", "type": "I", "score": 3},
            {"text": "Тщательно взвесив все за и против, не торопясь", "type": "S", "score": 3},
            {"text": "На основе детального анализа данных и фактов", "type": "C", "score": 3}
        ]
    },
    {
        "id": 2,
        "question": "В конфликтной ситуации в команде я:",
        "options": [
            {"text": "Беру инициативу и решаю проблему напрямую", "type": "D", "score": 3},
            {"text": "Стараюсь найти компромисс, который устроит всех", "type": "I", "score": 3},
            {"text": "Выслушиваю все стороны и ищу мирное решение", "type": "S", "score": 3},
            {"text": "Анализирую факты и предлагаю логичное решение", "type": "C", "score": 3}
        ]
    },
    {
        "id": 3,
        "question": "При постановке целей команде я:",
        "options": [
            {"text": "Ставлю амбициозные цели и требую их достижения", "type": "D", "score": 3},
            {"text": "Вдохновляю команду на достижение общих целей", "type": "I", "score": 3},
            {"text": "Устанавливаю реалистичные цели с учетом возможностей команды", "type": "S", "score": 3},
            {"text": "Определяю четкие, измеримые цели с конкретными критериями", "type": "C", "score": 3}
        ]
    },
    {
        "id": 4,
        "question": "Мой стиль коммуникации с подчиненными:",
        "options": [
            {"text": "Прямой и четкий, без лишних слов", "type": "D", "score": 3},
            {"text": "Дружелюбный и открытый, поощряю диалог", "type": "I", "score": 3},
            {"text": "Терпеливый и поддерживающий", "type": "S", "score": 3},
            {"text": "Точный и основанный на фактах", "type": "C", "score": 3}
        ]
    },
    {
        "id": 5,
        "question": "При планировании проектов я:",
        "options": [
            {"text": "Фокусируюсь на конечном результате и сроках", "type": "D", "score": 3},
            {"text": "Учитываю мнения всех участников команды", "type": "I", "score": 3},
            {"text": "Создаю стабильный план с минимальными рисками", "type": "S", "score": 3},
            {"text": "Разрабатываю детальный план с четкими этапами", "type": "C", "score": 3}
        ]
    },
    {
        "id": 6,
        "question": "Когда сотрудник делает ошибку, я:",
        "options": [
            {"text": "Сразу указываю на ошибку и требую исправления", "type": "D", "score": 3},
            {"text": "Обсуждаю ошибку в позитивном ключе и помогаю найти решение", "type": "I", "score": 3},
            {"text": "Терпеливо объясняю, как избежать подобных ошибок в будущем", "type": "S", "score": 3},
            {"text": "Анализирую причины ошибки и создаю процедуры для их предотвращения", "type": "C", "score": 3}
        ]
    },
    {
        "id": 7,
        "question": "В стрессовых ситуациях я:",
        "options": [
            {"text": "Беру контроль и быстро принимаю решения", "type": "D", "score": 3},
            {"text": "Поддерживаю команду и ищу творческие решения", "type": "I", "score": 3},
            {"text": "Остаюсь спокойным и стабилизирую ситуацию", "type": "S", "score": 3},
            {"text": "Систематически анализирую проблему и ищу оптимальное решение", "type": "C", "score": 3}
        ]
    },
    {
        "id": 8,
        "question": "Мой подход к мотивации сотрудников:",
        "options": [
            {"text": "Ставлю вызовы и поощряю конкуренцию", "type": "D", "score": 3},
            {"text": "Создаю позитивную атмосферу и признаю достижения", "type": "I", "score": 3},
            {"text": "Обеспечиваю стабильность и поддержку", "type": "S", "score": 3},
            {"text": "Предоставляю четкие критерии оценки и справедливое вознаграждение", "type": "C", "score": 3}
        ]
    },
    {
        "id": 9,
        "question": "При делегировании задач я:",
        "options": [
            {"text": "Даю четкие инструкции и жду результатов", "type": "D", "score": 3},
            {"text": "Объясняю важность задачи и вдохновляю на выполнение", "type": "I", "score": 3},
            {"text": "Убеждаюсь, что сотрудник готов и поддерживаю в процессе", "type": "S", "score": 3},
            {"text": "Предоставляю детальные инструкции и критерии качества", "type": "C", "score": 3}
        ]
    },
    {
        "id": 10,
        "question": "Мой стиль проведения совещаний:",
        "options": [
            {"text": "Эффективный и целенаправленный, фокус на результатах", "type": "D", "score": 3},
            {"text": "Интерактивный и вовлекающий, поощряю участие всех", "type": "I", "score": 3},
            {"text": "Структурированный и спокойный, даю всем высказаться", "type": "S", "score": 3},
            {"text": "Организованный и основанный на данных", "type": "C", "score": 3}
        ]
    },
    {
        "id": 11,
        "question": "При внедрении изменений в команде я:",
        "options": [
            {"text": "Быстро внедряю необходимые изменения", "type": "D", "score": 3},
            {"text": "Вовлекаю команду в процесс изменений", "type": "I", "score": 3},
            {"text": "Постепенно внедряю изменения, минимизируя стресс", "type": "S", "score": 3},
            {"text": "Планирую изменения поэтапно с четкими критериями", "type": "C", "score": 3}
        ]
    },
    {
        "id": 12,
        "question": "Мой подход к развитию сотрудников:",
        "options": [
            {"text": "Ставлю сложные задачи для быстрого роста", "type": "D", "score": 3},
            {"text": "Поощряю обучение через взаимодействие и обмен опытом", "type": "I", "score": 3},
            {"text": "Обеспечиваю постепенное развитие в комфортном темпе", "type": "S", "score": 3},
            {"text": "Создаю структурированные программы развития", "type": "C", "score": 3}
        ]
    }
]

@disc_bp.route('/questions', methods=['GET'])
@jwt_required()
def get_disc_questions():
    try:
        return jsonify({
            'success': True,
            'questions': DISC_QUESTIONS
        }), 200
    except Exception as e:
        logging.error(f"Error getting DISC questions: {str(e)}")
        return jsonify({'success': False, 'message': 'Ошибка при получении вопросов'}), 500

@disc_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_disc_assessment():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        answers = data.get('answers', {})
        
        if not answers:
            return jsonify({'success': False, 'message': 'Ответы не предоставлены'}), 400
        
        scores = calculate_disc_scores(answers)
        personality_type = determine_personality_type(scores)
        recommendations = generate_recommendations(personality_type, scores)
        
        assessment = DISCAssessment(
            user_id=user_id,
            dominance_score=scores['D'],
            influence_score=scores['I'],
            steadiness_score=scores['S'],
            conscientiousness_score=scores['C'],
            personality_type=personality_type,
            recommendations=recommendations,
            answers=answers
        )
        
        db.session.add(assessment)
        
        user = User.query.get(user_id)
        if user:
            user.personality_type = personality_type
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'assessment': assessment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error submitting DISC assessment: {str(e)}")
        return jsonify({'success': False, 'message': 'Ошибка при сохранении результатов'}), 500

@disc_bp.route('/history', methods=['GET'])
@jwt_required()
def get_assessment_history():
    try:
        user_id = get_jwt_identity()
        assessments = DISCAssessment.query.filter_by(user_id=user_id).order_by(DISCAssessment.completed_at.desc()).all()
        
        return jsonify({
            'success': True,
            'assessments': [assessment.to_dict() for assessment in assessments]
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting assessment history: {str(e)}")
        return jsonify({'success': False, 'message': 'Ошибка при получении истории'}), 500

@disc_bp.route('/latest', methods=['GET'])
@jwt_required()
def get_latest_assessment():
    try:
        user_id = get_jwt_identity()
        assessment = DISCAssessment.query.filter_by(user_id=user_id).order_by(DISCAssessment.completed_at.desc()).first()
        
        if not assessment:
            return jsonify({'success': False, 'message': 'Оценка не найдена'}), 404
        
        return jsonify({
            'success': True,
            'assessment': assessment.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting latest assessment: {str(e)}")
        return jsonify({'success': False, 'message': 'Ошибка при получении результатов'}), 500

def calculate_disc_scores(answers):
    scores = {'D': 0, 'I': 0, 'S': 0, 'C': 0}
    
    for question_id, selected_option in answers.items():
        question = next((q for q in DISC_QUESTIONS if q['id'] == int(question_id)), None)
        if question:
            option = next((opt for opt in question['options'] if opt['text'] == selected_option), None)
            if option:
                scores[option['type']] += option['score']
    
    return scores

def determine_personality_type(scores):
    max_score = max(scores.values())
    dominant_types = [type_name for type_name, score in scores.items() if score == max_score]
    
    if len(dominant_types) == 1:
        return dominant_types[0]
    else:
        type_combinations = {
            ('D', 'I'): 'DI',
            ('D', 'S'): 'DS',
            ('D', 'C'): 'DC',
            ('I', 'S'): 'IS',
            ('I', 'C'): 'IC',
            ('S', 'C'): 'SC'
        }
        
        sorted_types = tuple(sorted(dominant_types))
        return type_combinations.get(sorted_types, dominant_types[0])

def generate_recommendations(personality_type, scores):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt = f"""
        Как эксперт по развитию лидерских качеств, проанализируй результаты DISC-оценки менеджера:
        
        Тип личности: {personality_type}
        Баллы: Доминирование={scores['D']}, Влияние={scores['I']}, Стабильность={scores['S']}, Добросовестность={scores['C']}
        
        Предоставь общие рекомендации для развития как менеджера в следующих областях:
        1. Сильные стороны лидерства
        2. Области для развития
        3. Рекомендации по коммуникации с командой
        4. Советы по принятию решений
        5. Развитие эмоционального интеллекта
        
        Ответ должен быть на русском языке, структурированным и практичным.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logging.error(f"Error generating recommendations: {str(e)}")
        return f"Рекомендации для типа {personality_type}: Развивайте свои лидерские качества, работайте над коммуникацией с командой и продолжайте самосовершенствование."
