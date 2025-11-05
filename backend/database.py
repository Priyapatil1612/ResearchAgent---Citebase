"""
Database configuration and models for the Research Agent API.
"""

from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database URL - use environment variable for production
# Resolve to an absolute path by default to avoid multiple DB files from changing CWD
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_DB_PATH = os.path.join(_BACKEND_DIR, "research_agent.db")
_DB_PATH = os.getenv("DATABASE_PATH", _DEFAULT_DB_PATH)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DB_PATH}")

# Create engine
engine = create_engine(DATABASE_URL, echo=False)
print(f"[DB] Using database at: {_DB_PATH}")

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    topic = Column(String, nullable=False)
    namespace = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    research_summary = Column(JSON)
    status = Column(String, default="created")
    user_id = Column(String, nullable=False)  # For multi-tenancy

class Notebook(Base):
    __tablename__ = "notebooks"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    notes = Column(Text)  # Notebook-level notes (Markdown)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String, nullable=False)  # For multi-tenancy
    
    # Relationship
    entries = relationship("NotebookEntry", back_populates="notebook", cascade="all, delete-orphan")

class NotebookEntry(Base):
    __tablename__ = "notebook_entries"
    
    id = Column(String, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    citations = Column(JSON)
    project_id = Column(String, ForeignKey("projects.id"))
    notebook_id = Column(String, ForeignKey("notebooks.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String, nullable=False)  # For multi-tenancy
    notes = Column(Text)  # Per-entry personal notes (plain text)
    entry_type = Column(String, nullable=False, default="qa")  # type of entry (e.g., 'qa')
    
    # Relationships
    notebook = relationship("Notebook", back_populates="entries")
    project = relationship("Project")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id"), index=True, nullable=False)
    role = Column(String, nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    citations = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String, nullable=False)

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)
    # Lightweight migration for existing DBs: add 'notes' columns if missing
    with engine.connect() as conn:
        # Use exec_driver_sql in SQLAlchemy 2.0 for driver-level SQL (PRAGMA/DDL)
        # Check notebooks.notes
        res = conn.exec_driver_sql("PRAGMA table_info('notebooks')").fetchall()
        notebook_cols = {row[1] for row in res}
        if 'notes' not in notebook_cols:
            conn.exec_driver_sql("ALTER TABLE notebooks ADD COLUMN notes TEXT")
        # Check notebook_entries.notes
        res = conn.exec_driver_sql("PRAGMA table_info('notebook_entries')").fetchall()
        entry_cols = {row[1] for row in res}
        if 'notes' not in entry_cols:
            conn.exec_driver_sql("ALTER TABLE notebook_entries ADD COLUMN notes TEXT")
        # Ensure entry_type exists with a default to satisfy NOT NULL
        if 'entry_type' not in entry_cols:
            conn.exec_driver_sql("ALTER TABLE notebook_entries ADD COLUMN entry_type TEXT DEFAULT 'qa' NOT NULL")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")

