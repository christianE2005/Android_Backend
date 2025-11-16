import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Base class for models
Base = declarative_base()

def get_database_url():
    """Get database URL from environment variables"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Default to SQLite for development if no DATABASE_URL is set
        return "sqlite:///./app.db"
    
    # Convert mysql:// to mysql+pymysql://
    if database_url.startswith("mysql://"):
        database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
    
    return database_url

# Create engine
database_url = get_database_url()
if database_url.startswith("sqlite"):
    # SQLite doesn't need SSL
    engine = create_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False}
    )
elif database_url.startswith("mysql"):
    # MySQL with SSL (Aiven requires SSL)
    engine = create_engine(
        database_url,
        echo=False,
        connect_args={
            "ssl": {"check_hostname": False, "verify_mode": False}
        }
    )
else:
    # PostgreSQL with SSL for Supabase
    engine = create_engine(
        database_url,
        echo=False,
        connect_args={
            "sslmode": "require"
        }
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def connect_and_sync():
    """Connect to database and create tables"""
    try:
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Import models to register them
        from models.user import Usuario
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✓ Database connected and synchronized")
        return {"Usuario": Usuario}
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        raise
