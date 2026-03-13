from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

Engine = create_engine(
	settings.database_url,
	pool_pre_ping=True,
)

SessionLocal = sessionmaker(
	autocommit=False,
	autoflush=False,
	bind=Engine,
)

Base = declarative_base()

def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()