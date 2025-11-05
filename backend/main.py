"""
FastAPI Backend for Research Agent
Provides REST API for project management, research, and notebook functionality.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import sys
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent_react import ResearchAgent
from config.settings import SETTINGS
from database import get_db, create_tables, Project as ProjectModel, Notebook as NotebookModel, NotebookEntry as NotebookEntryModel, User as UserModel
from database import ChatMessage as ChatMessageModel

# Initialize FastAPI app
app = FastAPI(
    title="Research Agent API",
    description="API for managing research projects and notebooks",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-vercel-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Password hashing and JWT setup
from passlib.context import CryptContext
# JWT compatibility shim: prefer PyJWT, fallback to python-jose
try:
    import jwt as _pyjwt  # PyJWT
    from jwt import ExpiredSignatureError as JWTExpiredError
    from jwt import InvalidTokenError as JWTInvalidError
    def jwt_encode(payload, secret, algorithm):
        return _pyjwt.encode(payload, secret, algorithm=algorithm)
    def jwt_decode(token, secret, algorithms):
        algs = [algorithms] if isinstance(algorithms, str) else algorithms
        # Disable iat verification and allow small leeway for clock skew
        return _pyjwt.decode(
            token,
            secret,
            algorithms=algs,
            options={"verify_iat": False},
            leeway=30,
        )
except Exception:
    from jose import jwt as _pyjwt  # python-jose
    from jose.exceptions import ExpiredSignatureError as JWTExpiredError
    from jose.exceptions import JWTError as JWTInvalidError
    def jwt_encode(payload, secret, algorithm):
        return _pyjwt.encode(payload, secret, algorithm=algorithm)
    def jwt_decode(token, secret, algorithms):
        algs = [algorithms] if isinstance(algorithms, str) else algorithms
        # Disable iat verification and allow small leeway for clock skew
        return _pyjwt.decode(
            token,
            secret,
            algorithms=algs,
            options={"verify_iat": False},
            leeway=30,
        )

# Use Argon2 for password hashing to avoid bcrypt 72-byte limit
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "43200"))  # default 30 days

# Initialize research agent
research_agent = ResearchAgent()

# Create database tables
create_tables()

# Pydantic models
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    topic: str
    namespace: Optional[str] = None

class Project(BaseModel):
    id: str
    name: str
    description: Optional[str]
    topic: str
    namespace: str
    created_at: datetime
    last_accessed: datetime
    research_summary: Optional[Dict[str, Any]] = None
    status: str = "created"  # created, researching, completed, error

class QuestionRequest(BaseModel):
    question: str
    top_k: Optional[int] = 6

class QuestionResponse(BaseModel):
    answer: str
    citations: List[Dict[str, str]]
    trace: List[str]

class NotebookCreate(BaseModel):
    name: str
    description: Optional[str] = None

class Notebook(BaseModel):
    id: str
    name: str
    description: Optional[str]
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    entries: List[Dict[str, Any]] = []

class NotebookEntry(BaseModel):
    question: str
    answer: str
    citations: List[Dict[str, str]]
    project_id: str
    notes: Optional[str] = None

# Database operations will be handled through SQLAlchemy ORM

class NotebookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class NotebookEntryUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    citations: Optional[List[Dict[str, str]]] = None
    notes: Optional[str] = None

# Auth models and helpers
class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: str
    email: str
    created_at: datetime

def _bcrypt_safe(password: str) -> str:
    # bcrypt only uses the first 72 bytes; truncate in UTF-8 bytes space to avoid errors
    # decode with 'ignore' to drop any split multibyte trailing sequence
    return password.encode('utf-8')[:72].decode('utf-8', 'ignore')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(user_id: str, email: str) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "email": email,
        # omit iat to avoid 'not yet valid' issues; exp is sufficient
        "exp": int((now + timedelta(minutes=JWT_EXPIRES_MIN)).timestamp()),
    }
    return jwt_encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

# Authentication dependency
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt_decode(token, JWT_SECRET, algorithms=JWT_ALGO)
        user_id = payload.get("sub")
        if not user_id:
            print("[AUTH] Missing sub in token payload")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        # Fetch from DB using injected session (by id only)
        db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            print(f"[AUTH] User not found for token sub={user_id}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return {"user_id": db_user.id, "email": db_user.email}
    except JWTExpiredError as e:
        print(f"[AUTH] Token expired: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except JWTInvalidError as e:
        print(f"[AUTH] Invalid token: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception as e:
        print(f"[AUTH] Unexpected auth error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# Public routes will not use auth; otherwise require get_current_user

# Auth endpoints
@app.post("/api/auth/signup", response_model=TokenResponse)
async def signup(signup: SignupRequest, db: Session = Depends(get_db)):
    email_norm = signup.email.strip().lower()
    existing = db.query(UserModel).filter(UserModel.email == email_norm).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    user = UserModel(id=user_id, email=email_norm, password_hash=hash_password(signup.password))
    db.add(user)
    db.commit()
    token = create_access_token(user_id=user.id, email=user.email)
    return TokenResponse(access_token=token)

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(login: LoginRequest, db: Session = Depends(get_db)):
    email_norm = login.email.strip().lower()
    user = db.query(UserModel).filter(UserModel.email == email_norm).first()
    if not user or not verify_password(login.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user_id=user.id, email=user.email)
    return TokenResponse(access_token=token)

@app.get("/api/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(id=user.id, email=user.email, created_at=user.created_at)

# Project endpoints
@app.post("/api/projects", response_model=Project)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new research project."""
    project_id = str(uuid.uuid4())
    namespace = project_data.namespace or f"project_{project_id[:8]}"
    
    # Check if namespace already exists
    existing_project = db.query(ProjectModel).filter(ProjectModel.namespace == namespace).first()
    if existing_project:
        raise HTTPException(status_code=400, detail="Namespace already exists")
    
    db_project = ProjectModel(
        id=project_id,
        name=project_data.name,
        description=project_data.description,
        topic=project_data.topic,
        namespace=namespace,
        user_id=current_user["user_id"]
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return Project(
        id=db_project.id,
        name=db_project.name,
        description=db_project.description,
        topic=db_project.topic,
        namespace=db_project.namespace,
        created_at=db_project.created_at,
        last_accessed=db_project.last_accessed,
        research_summary=db_project.research_summary,
        status=db_project.status
    )

@app.get("/api/projects", response_model=List[Project])
async def get_projects(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all projects for the current user."""
    db_projects = db.query(ProjectModel).filter(ProjectModel.user_id == current_user["user_id"]).all()
    
    return [
        Project(
            id=p.id,
            name=p.name,
            description=p.description,
            topic=p.topic,
            namespace=p.namespace,
            created_at=p.created_at,
            last_accessed=p.last_accessed,
            research_summary=p.research_summary,
            status=p.status
        ) for p in db_projects
    ]

@app.get("/api/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific project."""
    db_project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.user_id == current_user["user_id"]
    ).first()
    
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update last accessed
    db_project.last_accessed = datetime.utcnow()
    db.commit()
    
    return Project(
        id=db_project.id,
        name=db_project.name,
        description=db_project.description,
        topic=db_project.topic,
        namespace=db_project.namespace,
        created_at=db_project.created_at,
        last_accessed=db_project.last_accessed,
        research_summary=db_project.research_summary,
        status=db_project.status
    )

@app.post("/api/projects/{project_id}/research")
async def start_research(
    project_id: str,
    force: bool = False,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start research for a project."""
    db_project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.user_id == current_user["user_id"]
    ).first()
    
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update status to researching
    db_project.status = "researching"
    db.commit()
    
    try:
        # Perform research using the existing agent
        result = research_agent.research(
            topic=db_project.topic,
            namespace=db_project.namespace,
            force=force
        )
        
        db_project.research_summary = {
            "indexed_pages": result.get("ingest_summary", {}).get("indexed_pages", 0),
            "indexed_chunks": result.get("ingest_summary", {}).get("indexed_chunks", 0),
            "sources": result.get("ingest_summary", {}).get("sources", []),
            "did_ingest": result.get("did_ingest", False)
        }
        db_project.status = "completed"
        db.commit()
        
        return {
            "message": "Research completed successfully",
            "result": result
        }
    except Exception as e:
        db_project.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

@app.post("/api/projects/{project_id}/ask", response_model=QuestionResponse)
async def ask_question(
    project_id: str,
    question_data: QuestionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ask a question about a project."""
    db_project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.user_id == current_user["user_id"]
    ).first()
    
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if db_project.status != "completed":
        raise HTTPException(status_code=400, detail="Project research not completed")
    
    try:
        # persist user question
        user_msg = ChatMessageModel(
            id=str(uuid.uuid4()),
            project_id=project_id,
            role="user",
            content=question_data.question,
            citations=None,
            user_id=current_user["user_id"],
        )
        db.add(user_msg)
        db.commit()
        result = research_agent.ask(
            question=question_data.question,
            namespace=db_project.namespace,
            top_k=question_data.top_k
        )
        # persist assistant answer
        asst_msg = ChatMessageModel(
            id=str(uuid.uuid4()),
            project_id=project_id,
            role="assistant",
            content=result["content"],
            citations=result.get("citations", []),
            user_id=current_user["user_id"],
        )
        db.add(asst_msg)
        db.commit()
        
        return QuestionResponse(
            answer=result["content"],
            citations=result["citations"],
            trace=result["trace"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get answer: {str(e)}")

# Project chat history endpoints
@app.get("/api/projects/{project_id}/chats")
async def get_project_chats(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.user_id == current_user["user_id"]
    ).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    msgs = (
        db.query(ChatMessageModel)
        .filter(ChatMessageModel.project_id == project_id, ChatMessageModel.user_id == current_user["user_id"])
        .order_by(ChatMessageModel.created_at.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "type": m.role,
            "content": m.content,
            "citations": m.citations or [],
            "timestamp": m.created_at.isoformat(),
        }
        for m in msgs
    ]

# Notebook endpoints
@app.post("/api/notebooks", response_model=Notebook)
async def create_notebook(
    notebook_data: NotebookCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new notebook."""
    notebook_id = str(uuid.uuid4())
    
    db_notebook = NotebookModel(
        id=notebook_id,
        name=notebook_data.name,
        description=notebook_data.description,
        user_id=current_user["user_id"]
    )
    
    db.add(db_notebook)
    db.commit()
    db.refresh(db_notebook)
    
    return Notebook(
        id=db_notebook.id,
        name=db_notebook.name,
        description=db_notebook.description,
        created_at=db_notebook.created_at,
        updated_at=db_notebook.updated_at,
        entries=[]
    )

@app.get("/api/notebooks", response_model=List[Notebook])
async def get_notebooks(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all notebooks for the current user."""
    db_notebooks = db.query(NotebookModel).filter(NotebookModel.user_id == current_user["user_id"]).all()
    
    return [
        Notebook(
            id=n.id,
            name=n.name,
            description=n.description,
            notes=n.notes,
            created_at=n.created_at,
            updated_at=n.updated_at,
            entries=[
                {
                    "id": e.id,
                    "question": e.question,
                    "answer": e.answer,
                    "citations": e.citations or [],
                    "project_id": e.project_id,
                    "created_at": e.created_at.isoformat(),
                    "notes": e.notes,
                } for e in n.entries
            ]
        ) for n in db_notebooks
    ]

@app.get("/api/notebooks/{notebook_id}", response_model=Notebook)
async def get_notebook(
    notebook_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific notebook."""
    db_notebook = db.query(NotebookModel).filter(
        NotebookModel.id == notebook_id,
        NotebookModel.user_id == current_user["user_id"]
    ).first()
    
    if not db_notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    return Notebook(
        id=db_notebook.id,
        name=db_notebook.name,
        description=db_notebook.description,
        notes=db_notebook.notes,
        created_at=db_notebook.created_at,
        updated_at=db_notebook.updated_at,
        entries=[
            {
                "id": e.id,
                "question": e.question,
                "answer": e.answer,
                "citations": e.citations or [],
                "project_id": e.project_id,
                "created_at": e.created_at.isoformat(),
                "notes": e.notes,
            } for e in db_notebook.entries
        ]
    )

@app.post("/api/notebooks/{notebook_id}/entries")
async def add_notebook_entry(
    notebook_id: str,
    entry_data: NotebookEntry,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add an entry to a notebook."""
    # Check if notebook exists
    db_notebook = db.query(NotebookModel).filter(
        NotebookModel.id == notebook_id,
        NotebookModel.user_id == current_user["user_id"]
    ).first()
    
    if not db_notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    # Check if project exists
    db_project = db.query(ProjectModel).filter(
        ProjectModel.id == entry_data.project_id,
        ProjectModel.user_id == current_user["user_id"]
    ).first()
    
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    entry_id = str(uuid.uuid4())
    db_entry = NotebookEntryModel(
        id=entry_id,
        question=entry_data.question,
        answer=entry_data.answer,
        citations=entry_data.citations,
        project_id=entry_data.project_id,
        notebook_id=notebook_id,
        user_id=current_user["user_id"],
        notes=entry_data.notes,
        entry_type="qa",
    )
    
    db.add(db_entry)
    db_notebook.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": "Entry added successfully",
        "entry": {
            "id": db_entry.id,
            "question": db_entry.question,
            "answer": db_entry.answer,
            "citations": db_entry.citations or [],
            "project_id": db_entry.project_id,
            "created_at": db_entry.created_at.isoformat(),
            "notes": db_entry.notes,
        }
    }

@app.delete("/api/notebooks/{notebook_id}/entries/{entry_id}")
async def delete_notebook_entry(
    notebook_id: str,
    entry_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an entry from a notebook."""
    db_entry = db.query(NotebookEntryModel).filter(
        NotebookEntryModel.id == entry_id,
        NotebookEntryModel.notebook_id == notebook_id,
        NotebookEntryModel.user_id == current_user["user_id"]
    ).first()
    
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    db.delete(db_entry)
    
    # Update notebook timestamp
    db_notebook = db.query(NotebookModel).filter(NotebookModel.id == notebook_id).first()
    if db_notebook:
        db_notebook.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Entry deleted successfully"}

@app.patch("/api/notebooks/{notebook_id}", response_model=Notebook)
async def update_notebook(
    notebook_id: str,
    notebook_patch: NotebookUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notebook fields (e.g., notes, name, description)."""
    db_notebook = db.query(NotebookModel).filter(
        NotebookModel.id == notebook_id,
        NotebookModel.user_id == current_user["user_id"]
    ).first()
    if not db_notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    updated = False
    if notebook_patch.name is not None:
        db_notebook.name = notebook_patch.name
        updated = True
    if notebook_patch.description is not None:
        db_notebook.description = notebook_patch.description
        updated = True
    if notebook_patch.notes is not None:
        db_notebook.notes = notebook_patch.notes
        updated = True
    if updated:
        db_notebook.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_notebook)

    return Notebook(
        id=db_notebook.id,
        name=db_notebook.name,
        description=db_notebook.description,
        notes=db_notebook.notes,
        created_at=db_notebook.created_at,
        updated_at=db_notebook.updated_at,
        entries=[
            {
                "id": e.id,
                "question": e.question,
                "answer": e.answer,
                "citations": e.citations or [],
                "project_id": e.project_id,
                "created_at": e.created_at.isoformat(),
                "notes": e.notes,
            } for e in db_notebook.entries
        ]
    )

@app.patch("/api/notebooks/{notebook_id}/entries/{entry_id}")
async def update_notebook_entry(
    notebook_id: str,
    entry_id: str,
    entry_patch: NotebookEntryUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a notebook entry (e.g., notes)."""
    db_entry = db.query(NotebookEntryModel).filter(
        NotebookEntryModel.id == entry_id,
        NotebookEntryModel.notebook_id == notebook_id,
        NotebookEntryModel.user_id == current_user["user_id"]
    ).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    if entry_patch.question is not None:
        db_entry.question = entry_patch.question
    if entry_patch.answer is not None:
        db_entry.answer = entry_patch.answer
    if entry_patch.citations is not None:
        db_entry.citations = entry_patch.citations
    if entry_patch.notes is not None:
        db_entry.notes = entry_patch.notes

    # Update parent notebook timestamp
    db_notebook = db.query(NotebookModel).filter(NotebookModel.id == notebook_id).first()
    if db_notebook:
        db_notebook.updated_at = datetime.utcnow()

    db.commit()
    return {
        "id": db_entry.id,
        "question": db_entry.question,
        "answer": db_entry.answer,
        "citations": db_entry.citations or [],
        "project_id": db_entry.project_id,
        "created_at": db_entry.created_at.isoformat(),
        "notes": db_entry.notes,
    }

# Delete project
@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.user_id == current_user["user_id"]
    ).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    # delete chat messages for project
    db.query(ChatMessageModel).filter(ChatMessageModel.project_id == project_id, ChatMessageModel.user_id == current_user["user_id"]).delete()
    # delete notebook entries that reference this project
    db.query(NotebookEntryModel).filter(NotebookEntryModel.project_id == project_id, NotebookEntryModel.user_id == current_user["user_id"]).delete()
    # delete project
    db.delete(db_project)
    db.commit()
    return {"message": "Project deleted"}

# Delete notebook
@app.delete("/api/notebooks/{notebook_id}")
async def delete_notebook(
    notebook_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_notebook = db.query(NotebookModel).filter(
        NotebookModel.id == notebook_id,
        NotebookModel.user_id == current_user["user_id"]
    ).first()
    if not db_notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    db.delete(db_notebook)
    db.commit()
    return {"message": "Notebook deleted"}

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
