import pandas as pd
from app import app, db
from models import Question

# 📌 Путь к файлу
file_path = "C:\\Users\\epcsa\\Downloads\\Agile.xlsx"

# 📌 Загружаем данные
df = pd.read_excel(file_path, header=0)

# 🔹 Чистим названия колонок от лишних пробелов и переносов строк
df.columns = df.columns.str.strip().str.replace("\n", "")

# 🔹 Проверяем названия колонок
print("Названия колонок в файле:", df.columns.tolist())

# 🔹 Проверяем, есть ли нужные колонки
expected_columns = [
    "Категория", "Подкатегория", "Вопросы",
    "Базовый уровень", "Переходный уровень", "Растущий уровень",
    "Уровень нормализации", "Оптимальный уровень"
]
for col in expected_columns:
    if col not in df.columns:
        raise ValueError(f"❌ Ошибка: Колонка '{col}' отсутствует в файле!")

# 🔹 Загружаем вопросы с вариантами ответов
with app.app_context():
    for _, row in df.iterrows():
        category = row["Категория"]
        subcategory = row["Подкатегория"]
        question_text = row["Вопросы"]
        level_basic = row["Базовый уровень"]
        level_transitional = row["Переходный уровень"]
        level_growing = row["Растущий уровень"]
        level_normalization = row["Уровень нормализации"]
        level_optimal = row["Оптимальный уровень"]

        # Проверяем, что данные не пустые
        if pd.isna(category) or pd.isna(subcategory) or pd.isna(question_text):
            print(f"⚠️ Пропущена строка с пустыми данными: {row}")
            continue

        # Добавляем в базу
        question = Question(
            category=str(category).strip(),
            subcategory=str(subcategory).strip(),
            question=str(question_text).strip(),
            level_basic=str(level_basic).strip() if pd.notna(level_basic) else None,
            level_transitional=str(level_transitional).strip() if pd.notna(level_transitional) else None,
            level_growing=str(level_growing).strip() if pd.notna(level_growing) else None,
            level_normalization=str(level_normalization).strip() if pd.notna(level_normalization) else None,
            level_optimal=str(level_optimal).strip() if pd.notna(level_optimal) else None,
        )

        db.session.add(question)

    db.session.commit()
    print("✅ Вопросы и ответы успешно загружены в базу данных!")

