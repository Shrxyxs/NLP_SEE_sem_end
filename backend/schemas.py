"""
schemas.py - Pydantic Models for API Request/Response
=====================================================
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ---------------------
# Evaluate
# ---------------------
class EvaluateRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Essay text to evaluate")
    prompt_id: int = Field(default=1, ge=1, le=8, description="ASAP prompt ID (1-8)")
    title: Optional[str] = Field(default=None, description="Optional essay title")
    save: bool = Field(default=True, description="Whether to save to history")


class TraitScores(BaseModel):
    content_ideas: float
    organization: float
    language_use: float
    conventions: float
    vocabulary: float


class GrammarError(BaseModel):
    message: str
    context: str
    offset: int
    length: int
    rule: str
    replacements: list[str]
    category: str


class EvaluateResponse(BaseModel):
    # Scoring
    score_100: float
    grade: str
    confidence: float
    raw_score: int
    raw_score_range: list[int]
    prompt_id: int

    # Traits
    traits: TraitScores
    trait_total: float
    trait_max: int = 100

    # Grammar
    grammar_errors: list[GrammarError]
    grammar_error_count: int

    # Text stats
    word_count: int
    char_count: int
    sentence_count: int
    paragraph_count: int
    unique_words: int
    language_detected: str
    writing_consistency: int

    # Readability
    readability: dict

    # Analytics
    analytics: dict

    # Essay reference
    essay_id: Optional[int] = None


# ---------------------
# Essay CRUD
# ---------------------
class EssayListItem(BaseModel):
    id: int
    title: str
    language: str
    word_count: int
    score_100: float
    grade: str
    created_at: str

    class Config:
        from_attributes = True


class EssayDetail(BaseModel):
    id: int
    title: str
    text: str
    language: str
    prompt_id: int
    score_100: float
    grade: str
    confidence: float
    traits: dict
    grammar_error_count: int
    word_count: int
    char_count: int
    writing_consistency: int
    analytics: dict
    readability: dict
    created_at: str

    class Config:
        from_attributes = True


# ---------------------
# Dashboard
# ---------------------
class DashboardStats(BaseModel):
    average_score: float
    essays_evaluated: int
    best_grade: str
    best_essay_title: str
    recent_essays: list[EssayListItem]
    skill_breakdown: dict
    improvement_plan: dict


# ---------------------
# Analytics
# ---------------------
class AnalyticsResponse(BaseModel):
    metrics: dict
    score_progress: list[dict]
    writing_consistency: int
    total_essays: int
