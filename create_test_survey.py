from app import app, db
from models import Survey
import uuid
import json

def create_test_survey():
    with app.app_context():
        db.create_all()
        
        test_survey = Survey(
            title='Test E-NPS Survey',
            survey_type='enps',
            creator_id=1,
            team_id=1,
            access_token=str(uuid.uuid4()),
            questions=[
                {'id': 1, 'type': 'radio', 'question': 'Укажите ваш формат работы:', 'options': ['Офисный', 'Удаленный', 'Гибридный'], 'required': True},
                {'id': 2, 'type': 'scale', 'question': 'Порекомендовали бы вы работать здесь своим друзьям?', 'scale': [1,2,3,4,5], 'required': True}
            ],
            status='active'
        )
        
        db.session.add(test_survey)
        db.session.commit()
        
        print(f'Created test survey with token: {test_survey.access_token}')
        return test_survey.access_token

if __name__ == '__main__':
    token = create_test_survey()
    print(f'Test survey URL: http://localhost:5000/survey/{token}')
