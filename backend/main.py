"""
main.py - FastAPI Application
==============================
SahityaAI Backend: Essay evaluation with BERT scoring + text analysis.

Run: uvicorn backend.main:app --reload --port 8000
"""

import os
import sys
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Add parent dir to path so we can import lang_detector
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from scorer import EssayScorerService
from analyzer import analyze_essay
from database import get_db, init_db
from models import Essay
from schemas import (
    EvaluateRequest, EvaluateResponse,
    EssayListItem, EssayDetail,
    DashboardStats, AnalyticsResponse,
)

# Import lang detector from parent directory
from lang_detector import detect_language

# ---------------------
# Config
# ---------------------
CHECKPOINT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "bert_all_prompts_best.pt"
)


# ---------------------
# Lifespan (startup/shutdown)
# ---------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[App] Starting SahityaAI backend...")
    init_db()

    scorer = EssayScorerService.get_instance()
    scorer.load(CHECKPOINT_PATH)

    yield

    # Shutdown
    print("[App] Shutting down...")


# ---------------------
# App
# ---------------------
app = FastAPI(
    title="SahityaAI",
    description="Bilingual Essay Evaluation Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
        "http://localhost:5175", "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# POST /api/evaluate
# =====================
@app.post("/api/evaluate", response_model=EvaluateResponse)
def evaluate_essay(req: EvaluateRequest, db: Session = Depends(get_db)):
    """Score an essay using BERT and analyze text traits."""

    # Detect language
    lang = detect_language(req.text)

    # Score with BERT/MuRIL depending on language
    scorer = EssayScorerService.get_instance()
    score_result = scorer.score_essay(
        text=req.text,
        prompt_id=req.prompt_id,
        language=lang,
    )

    # Analyze text
    analysis = analyze_essay(req.text)

    # Build response
    response = {
        **score_result,
        "traits": analysis["traits"],
        "trait_total": analysis["trait_total"],
        "trait_max": analysis["trait_max"],
        "grammar_errors": analysis["grammar_errors"],
        "grammar_error_count": analysis["grammar_error_count"],
        "word_count": analysis["word_count"],
        "char_count": analysis["char_count"],
        "sentence_count": analysis["sentence_count"],
        "paragraph_count": analysis["paragraph_count"],
        "unique_words": analysis["unique_words"],
        "language_detected": lang,
        "writing_consistency": analysis["writing_consistency"],
        "readability": analysis["readability"],
        "analytics": analysis["analytics"],
    }

    # Save to DB if requested
    if req.save:
        title = req.title or _generate_title(req.text)
        essay = Essay(
            title=title,
            text=req.text,
            language=lang,
            prompt_id=req.prompt_id,
            score_100=score_result["score_100"],
            grade=score_result["grade"],
            confidence=score_result["confidence"],
            traits_json=json.dumps(analysis["traits"]),
            grammar_error_count=analysis["grammar_error_count"],
            word_count=analysis["word_count"],
            char_count=analysis["char_count"],
            writing_consistency=analysis["writing_consistency"],
            analytics_json=json.dumps(analysis["analytics"]),
            readability_json=json.dumps(analysis["readability"]),
        )
        db.add(essay)
        db.commit()
        db.refresh(essay)
        response["essay_id"] = essay.id

    return response


def _generate_title(text: str) -> str:
    """Generate a title from the first sentence of the essay."""
    # Take first sentence or first 50 chars
    first_line = text.strip().split('.')[0].split('\n')[0]
    if len(first_line) > 60:
        first_line = first_line[:57] + "..."
    return first_line or "Untitled Essay"


# =====================
# GET /api/essays
# =====================
@app.get("/api/essays", response_model=list[EssayListItem])
def list_essays(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List saved essays, most recent first."""
    essays = (
        db.query(Essay)
        .order_by(desc(Essay.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [e.to_list_item() for e in essays]


# =====================
# GET /api/essays/{id}
# =====================
@app.get("/api/essays/{essay_id}", response_model=EssayDetail)
def get_essay(essay_id: int, db: Session = Depends(get_db)):
    """Get a single essay with full results."""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="Essay not found")
    
    # Run conventions check dynamically since we don't save the full JSON of errors in DB
    from analyzer import score_conventions
    conventions = score_conventions(essay.text)
    
    res = essay.to_detail()
    res["grammar_errors"] = conventions["errors"]
    return res


# =====================
# DELETE /api/essays/{id}
# =====================
@app.delete("/api/essays/{essay_id}")
def delete_essay(essay_id: int, db: Session = Depends(get_db)):
    """Delete an essay."""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="Essay not found")
    db.delete(essay)
    db.commit()
    return {"ok": True, "deleted_id": essay_id}


# =====================
# GET /api/dashboard
# =====================
@app.get("/api/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    """Get dashboard summary statistics."""
    essays = db.query(Essay).order_by(desc(Essay.created_at)).all()

    if not essays:
        return {
            "average_score": 0,
            "essays_evaluated": 0,
            "best_grade": "N/A",
            "best_essay_title": "",
            "recent_essays": [],
            "skill_breakdown": {
                "content_ideas": 0,
                "organization": 0,
                "language_use": 0,
                "conventions": 0,
                "vocabulary": 0,
            },
            "improvement_plan": {
                "strengths": [],
                "focus_areas": [],
            },
        }

    # Compute averages
    avg_score = sum(e.score_100 for e in essays) / len(essays)
    best = max(essays, key=lambda e: e.score_100)

    # Average trait scores across all essays
    trait_totals = {"content_ideas": 0, "organization": 0, "language_use": 0,
                    "conventions": 0, "vocabulary": 0}
    for e in essays:
        traits = e.traits
        for key in trait_totals:
            trait_totals[key] += traits.get(key, 0)
    trait_avgs = {k: round(v / len(essays), 1) for k, v in trait_totals.items()}

    # Generate improvement plan based on trait scores
    trait_pct = {k: round(v / 20 * 100) for k, v in trait_avgs.items()}
    sorted_traits = sorted(trait_pct.items(), key=lambda x: x[1], reverse=True)

    trait_labels = {
        "content_ideas": "Content & Ideas",
        "organization": "Organization",
        "language_use": "Language Use",
        "conventions": "Grammar & Conventions",
        "vocabulary": "Vocabulary",
    }

    strengths = [
        f"Strong {trait_labels[k].lower()} in your essays"
        for k, v in sorted_traits[:2]
    ]
    focus_areas = [
        f"Improve {trait_labels[k].lower()} (currently {v}%)"
        for k, v in sorted_traits[-2:]
    ]

    # Skill breakdown as percentages
    skill_breakdown = {k: round(v / 20 * 100) for k, v in trait_avgs.items()}

    return {
        "average_score": round(avg_score, 1),
        "essays_evaluated": len(essays),
        "best_grade": best.grade,
        "best_essay_title": f"{best.language.title()} Essay #{best.id}",
        "recent_essays": [e.to_list_item() for e in essays[:5]],
        "skill_breakdown": skill_breakdown,
        "improvement_plan": {
            "strengths": strengths,
            "focus_areas": focus_areas,
        },
    }


# =====================
# GET /api/analytics
# =====================
@app.get("/api/analytics", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)):
    """Get aggregated writing analytics."""
    essays = db.query(Essay).order_by(Essay.created_at).all()

    if not essays:
        return {
            "metrics": {
                "vocabulary_richness": 0,
                "lexical_diversity": 0,
                "sentence_complexity": 0,
                "paragraph_balance": 0,
                "readability": 0,
                "repetition_detection": 0,
            },
            "score_progress": [],
            "writing_consistency": 0,
            "total_essays": 0,
        }

    # Average analytics across all essays
    metric_keys = ["vocabulary_richness", "lexical_diversity", "sentence_complexity",
                   "paragraph_balance", "readability", "repetition_detection"]
    metric_totals = {k: 0 for k in metric_keys}

    for e in essays:
        analytics = e.analytics
        for k in metric_keys:
            metric_totals[k] += analytics.get(k, 0)

    avg_metrics = {k: round(v / len(essays)) for k, v in metric_totals.items()}

    # Score progress over time (group by week-like chunks)
    score_progress = []
    chunk_size = max(1, len(essays) // 8)
    for i in range(0, len(essays), chunk_size):
        chunk = essays[i:i+chunk_size]
        eng_scores = [e.score_100 for e in chunk if e.language == "english"]
        kan_scores = [e.score_100 for e in chunk if e.language == "kannada"]
        entry = {
            "label": f"Week {len(score_progress) + 1}",
            "english": round(sum(eng_scores) / len(eng_scores), 1) if eng_scores else 0,
            "kannada": round(sum(kan_scores) / len(kan_scores), 1) if kan_scores else 0,
        }
        score_progress.append(entry)

    avg_consistency = round(
        sum(e.writing_consistency for e in essays) / len(essays)
    )

    return {
        "metrics": avg_metrics,
        "score_progress": score_progress,
        "writing_consistency": avg_consistency,
        "total_essays": len(essays),
    }


# =====================
# Health check
# =====================
@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": EssayScorerService.get_instance()._loaded}
