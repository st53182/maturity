from app import app
from database import db
from models import SurveyTemplate
from surveys import ENPS_TEMPLATE, FEEDBACK_360_TEMPLATE

def create_default_templates():
    with app.app_context():
        existing_enps = SurveyTemplate.query.filter_by(survey_type='enps', is_default=True).first()
        existing_360 = SurveyTemplate.query.filter_by(survey_type='360', is_default=True).first()
        
        if not existing_enps:
            enps_template = SurveyTemplate(
                name="Стандартный e-NPS опросник",
                survey_type="enps",
                creator_id=None,
                questions=ENPS_TEMPLATE,
                is_default=True
            )
            db.session.add(enps_template)
        
        if not existing_360:
            feedback_360_template = SurveyTemplate(
                name="Стандартный 360° опросник",
                survey_type="360",
                creator_id=None,
                questions=FEEDBACK_360_TEMPLATE,
                is_default=True
            )
            db.session.add(feedback_360_template)
        
        db.session.commit()
        print("Default templates created successfully")

if __name__ == '__main__':
    create_default_templates()
