from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# PostgreSQL database URL
DATABASE_URL = "postgresql://santamonica:npg_ykHrdc3LE8FS@ep-lively-dawn-a4n0qvmn.us-east-1.pg.koyeb.app/koyebdb"

# Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Ensure connections are validated before use
)

# Configure the session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Define the base class for ORM models
Base = declarative_base()


def init_db():
    """Initialize the database schema."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Database initialization failed: {e}")


def get_db() -> Generator[Session, None, None]:
    """Provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
