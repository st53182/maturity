import psycopg2
import os
from openai import OpenAI

DATABASE_URL = "postgresql://scrum_db_user:uX72DYTJ1HcKOWgqRnzTNMcXUvsYq8n0@dpg-cvl4rlggjchc73fqa0lg-a.frankfurt-postgres.render.com/scrum_db"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def translate_text(text, context=""):
    """Translate Russian text to English using OpenAI"""
    if not text or text.strip() == "":
        return ""
    
    prompt = f"""Translate the following Russian text to English. This is for a team maturity assessment questionnaire.
    
Context: {context}
Russian text: {text}

Provide only the English translation, no explanations."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional translator specializing in business and team management terminology."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return ""

def add_english_translations():
    """Add English translations to existing questions"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                ALTER TABLE question 
                ADD COLUMN IF NOT EXISTS category_en VARCHAR(255),
                ADD COLUMN IF NOT EXISTS subcategory_en VARCHAR(255),
                ADD COLUMN IF NOT EXISTS question_en TEXT,
                ADD COLUMN IF NOT EXISTS level_basic_en TEXT,
                ADD COLUMN IF NOT EXISTS level_transitional_en TEXT,
                ADD COLUMN IF NOT EXISTS level_growing_en TEXT,
                ADD COLUMN IF NOT EXISTS level_normalization_en TEXT,
                ADD COLUMN IF NOT EXISTS level_optimal_en TEXT;
            """)
            conn.commit()
            print("Added English columns to question table")
        except Exception as e:
            print(f"Columns might already exist: {e}")
        
        cur.execute("""
            SELECT id, category, subcategory, question, 
                   level_basic, level_transitional, level_growing, 
                   level_normalization, level_optimal
            FROM question 
            WHERE category_en IS NULL OR category_en = ''
        """)
        
        questions = cur.fetchall()
        print(f"Found {len(questions)} questions to translate")
        
        for i, (q_id, category, subcategory, question, basic, transitional, growing, normalization, optimal) in enumerate(questions):
            print(f"Translating question {i+1}/{len(questions)}: {q_id}")
            
            category_en = translate_text(category, "category name")
            subcategory_en = translate_text(subcategory, "subcategory name")
            question_en = translate_text(question, "assessment question")
            
            basic_en = translate_text(basic, "basic maturity level description")
            transitional_en = translate_text(transitional, "transitional maturity level description")
            growing_en = translate_text(growing, "growing maturity level description")
            normalization_en = translate_text(normalization, "normalization maturity level description")
            optimal_en = translate_text(optimal, "optimal maturity level description")
            
            cur.execute("""
                UPDATE question 
                SET category_en = %s, subcategory_en = %s, question_en = %s,
                    level_basic_en = %s, level_transitional_en = %s, 
                    level_growing_en = %s, level_normalization_en = %s, 
                    level_optimal_en = %s
                WHERE id = %s
            """, (category_en, subcategory_en, question_en, basic_en, 
                  transitional_en, growing_en, normalization_en, optimal_en, q_id))
            
            conn.commit()
            print(f"Updated question {q_id}")
        
        print("All translations completed successfully!")
        
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_english_translations()
