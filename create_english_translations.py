import os
from app import app, db
from models import Question

SAMPLE_TRANSLATIONS = {
    "Планирование": "Planning",
    "Ретроспективы": "Retrospectives", 
    "Демо": "Demo",
    "Управление продуктом": "Product Management",
    "Техническое совершенство": "Technical Excellence",
    "Культура команды": "Team Culture",
    "Коммуникация": "Communication",
    "Процессы": "Processes",
    "Инструменты": "Tools",
    "Метрики": "Metrics"
}

def translate_questions():
    """Add English translations to existing questions"""
    with app.app_context():
        questions = Question.query.all()
        
        for question in questions:
            if not question.category_en:
                question.category_en = SAMPLE_TRANSLATIONS.get(question.category, question.category)
            
            if not question.subcategory_en:
                question.subcategory_en = SAMPLE_TRANSLATIONS.get(question.subcategory, question.subcategory)
            
            if not question.question_en:
                question.question_en = f"[EN] {question.question}"
            
            if not question.level_basic_en and question.level_basic:
                question.level_basic_en = f"[EN] {question.level_basic}"
            
            if not question.level_transitional_en and question.level_transitional:
                question.level_transitional_en = f"[EN] {question.level_transitional}"
                
            if not question.level_growing_en and question.level_growing:
                question.level_growing_en = f"[EN] {question.level_growing}"
                
            if not question.level_normalization_en and question.level_normalization:
                question.level_normalization_en = f"[EN] {question.level_normalization}"
                
            if not question.level_optimal_en and question.level_optimal:
                question.level_optimal_en = f"[EN] {question.level_optimal}"
        
        db.session.commit()
        print("✅ English translations added to questions!")

if __name__ == "__main__":
    translate_questions()
