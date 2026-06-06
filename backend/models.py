"""
models.py - SQLAlchemy ORM Models
==================================
"""

import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from .database import Base


class Essay(Base):
    __tablename__ = "essays"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, default="Untitled Essay")
    text = Column(Text, nullable=False)
    language = Column(String(20), nullable=False, default="english")
    prompt_id = Column(Integer, nullable=False, default=1)

    # Scores
    score_100 = Column(Float, nullable=False)
    grade = Column(String(5), nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)

    # Traits (stored as JSON string)
    traits_json = Column(Text, nullable=False, default="{}")

    # Grammar
    grammar_error_count = Column(Integer, nullable=False, default=0)

    # Text stats
    word_count = Column(Integer, nullable=False, default=0)
    char_count = Column(Integer, nullable=False, default=0)
    writing_consistency = Column(Integer, nullable=False, default=0)

    # Analytics (stored as JSON string)
    analytics_json = Column(Text, nullable=False, default="{}")
    readability_json = Column(Text, nullable=False, default="{}")

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def traits(self) -> dict:
        return json.loads(self.traits_json) if self.traits_json else {}

    @property
    def analytics(self) -> dict:
        return json.loads(self.analytics_json) if self.analytics_json else {}

    @property
    def readability(self) -> dict:
        return json.loads(self.readability_json) if self.readability_json else {}

    def to_list_item(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "language": self.language,
            "word_count": self.word_count,
            "score_100": self.score_100,
            "grade": self.grade,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }

    def to_detail(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "language": self.language,
            "prompt_id": self.prompt_id,
            "score_100": self.score_100,
            "grade": self.grade,
            "confidence": self.confidence,
            "traits": self.traits,
            "grammar_error_count": self.grammar_error_count,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "writing_consistency": self.writing_consistency,
            "analytics": self.analytics,
            "readability": self.readability,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }
