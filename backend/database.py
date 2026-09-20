import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
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
    
    # Auto-migrate missing columns for SQLite database
    if db_url.startswith("sqlite"):
        with engine.connect() as conn:
            # Check existing columns in deal_records
            try:
                res = conn.execute(text("PRAGMA table_info(deal_records)")).fetchall()
                existing_cols = {row[1] for row in res}
                
                columns_to_add = [
                    ("user_id", "VARCHAR"),
                    ("dtl_created", "FLOAT DEFAULT 0.0"),
                    ("pro_forma_leverage_ratio", "FLOAT DEFAULT 0.0"),
                    ("interest_coverage_ratio", "FLOAT DEFAULT 0.0")
                ]
                
                for col_name, col_type in columns_to_add:
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE deal_records ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception as e:
                pass

def get_session():
    with Session(engine) as session:
        yield session
