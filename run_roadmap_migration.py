"""
Скрипт для выполнения миграции таблицы roadmap
Добавляет колонки quarter_start и sprints_per_quarter
"""
from app import app
from database import db
import os

def run_migration():
    """Выполняет миграцию для добавления новых колонок в таблицу roadmap"""
    with app.app_context():
        database_url = os.getenv("DATABASE_URL", "sqlite:///maturity_local.db")
        
        if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
            # PostgreSQL
            from sqlalchemy import text
            
            try:
                # Проверяем, существуют ли колонки
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='roadmap' AND column_name IN ('quarter_start', 'sprints_per_quarter')
                """))
                existing_columns = [row[0] for row in result]
                
                # Добавляем quarter_start, если не существует
                if 'quarter_start' not in existing_columns:
                    print("Добавляем колонку quarter_start...")
                    db.session.execute(text("ALTER TABLE roadmap ADD COLUMN quarter_start VARCHAR(10)"))
                    db.session.commit()
                    print("✓ Колонка quarter_start добавлена")
                else:
                    print("✓ Колонка quarter_start уже существует")
                
                # Добавляем sprints_per_quarter, если не существует
                if 'sprints_per_quarter' not in existing_columns:
                    print("Добавляем колонку sprints_per_quarter...")
                    db.session.execute(text("ALTER TABLE roadmap ADD COLUMN sprints_per_quarter INTEGER DEFAULT 6"))
                    db.session.commit()
                    print("✓ Колонка sprints_per_quarter добавлена")
                else:
                    print("✓ Колонка sprints_per_quarter уже существует")
                
                # Устанавливаем значение по умолчанию для существующих записей
                print("Обновляем существующие записи...")
                db.session.execute(text("UPDATE roadmap SET sprints_per_quarter = 6 WHERE sprints_per_quarter IS NULL"))
                db.session.commit()
                print("✓ Миграция завершена успешно!")
                
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при выполнении миграции: {e}")
                raise
        else:
            # SQLite - используем db.create_all() для создания колонок
            print("SQLite база данных - используем db.create_all()...")
            db.create_all()
            print("✓ Миграция завершена успешно!")

if __name__ == "__main__":
    run_migration()
