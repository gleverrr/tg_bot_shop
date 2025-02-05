from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from config import Config

DATABASE_URL = Config.DATABASE_URL

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

def get_db_session():
    return Session()