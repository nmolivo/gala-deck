from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, DateTime, Index, Enum
from sqlalchemy.dialects.postgresql import JSON
from database import Base


# Enums for type safety
class ArcanaType(str, PyEnum):
    """Major or Minor Arcana"""
    MAJOR = "major"
    MINOR = "minor"


class SuitType(str, PyEnum):
    """Tarot suits (Minor Arcana only)"""
    WANDS = "wands"
    CUPS = "cups"
    SWORDS = "swords"
    PENTACLES = "pentacles"


class ElementType(str, PyEnum):
    """Elemental associations"""
    FIRE = "fire"
    WATER = "water"
    EARTH = "earth"
    AIR = "air"


class Card(Base):
    """
    Tarot card model with all metadata and generation prompts
    """
    __tablename__ = "cards"
    __table_args__ = (
        Index('idx_element_suit', 'element', 'suit'),  # Composite index for filtering by both
        Index('idx_arcana_number', 'arcana', 'number'),  # For sorting cards
    )

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Core identification
    name = Column(String(100), unique=True, nullable=False, index=True)
    arcana = Column(Enum(ArcanaType), nullable=False, index=True)
    number = Column(Integer, nullable=False)  # 0-21 for major, 1-14 for minor
    suit = Column(Enum(SuitType), nullable=True, index=True)  # NULL for major arcana
    element = Column(Enum(ElementType), nullable=False, index=True)
    keywords = Column(JSON, nullable=True)  # Array of keyword strings
    symbolism = Column(Text, nullable=True)  # Long description of imagery
    meaning_upright = Column(Text, nullable=True)
    meaning_reversed = Column(Text, nullable=True)
    prompt_template = Column(Text, nullable=False)  