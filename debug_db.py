from app import app
from models import db
from sqlalchemy import inspect

with app.app_context():
    print("DB URI:", app.config["SQLALCHEMY_DATABASE_URI"])
    insp = inspect(db.engine)
    print("Tables BEFORE:", insp.get_table_names())
    db.create_all()
    print("Tables AFTER:", inspect(db.engine).get_table_names())
