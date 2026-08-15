import os
from sqlmodel import SQLModel, create_engine, Session
from backend.config import settings

db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# Normalize postgresql:// scheme if provided by Supabase / Neon (some providers pass postgres://)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True
)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
