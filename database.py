from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# This creates a file called interview.db in your project folder
SQLALCHEMY_DATABASE_URL = "sqlite:///./interview.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# This function gives us a database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()