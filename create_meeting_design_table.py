from app import app
from database import db
from models import MeetingDesign

with app.app_context():
    db.create_all()
    print("Meeting design table created successfully!")
