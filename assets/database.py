"""
Database configuration and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment variable
# Format: postgresql://username:password@host:port/database
# Example: postgresql://user:pass@localhost:5432/tarot_db
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/tarot_mirror"
)

# Handle Render/Heroku postgres URLs (they use postgres:// instead of postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create SQLAlchemy engine
# echo=True will log all SQL statements (useful for debugging, turn off in production)
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for development to see SQL queries
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=10,  # Connection pool size
    max_overflow=20  # Max overflow connections
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all models
Base = declarative_base()


# Dependency for FastAPI routes
def get_db():
    """
    Database session dependency for FastAPI.
    
    Usage in FastAPI route:
        @app.get("/cards")
        def get_cards(db: Session = Depends(get_db)):
            cards = db.query(Card).all()
            return cards
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database (create all tables)
def init_db():
    """
    Create all tables in the database.
    Call this once on first deployment.
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


# Drop all tables (useful for development/testing)
def drop_db():
    """
    Drop all tables. Use with caution!
    """
    Base.metadata.drop_all(bind=engine)
    print("All database tables dropped!")