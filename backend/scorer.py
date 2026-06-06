"""
scorer.py - BERT Essay Scoring Inference Wrapper
=================================================
Loads the trained BertEssayScorer checkpoint and provides
a clean inference API for the FastAPI backend.
"""

import os
import sys
import torch
import torch.nn as nn
from transformers import BertTokenizer, BertModel

# ---------------------
# Score ranges per ASAP prompt
# ---------------------
SCORE_RANGES = {
    1: (2, 12), 2: (1, 6), 3: (0, 3), 4: (0, 3),
    5: (0, 4),  6: (0, 4), 7: (0, 30), 8: (0, 60),
}

GRADE_MAP = [
    (97, "A+"), (93, "A"), (90, "A-"),
    (87, "B+"), (83, "B"), (80, "B-"),
    (77, "C+"), (73, "C"), (70, "C-"),
    (67, "D+"), (63, "D"), (60, "D-"),
    (0,  "F"),
]


def score_to_grade(score_100: float) -> str:
    """Convert a 0-100 score to a letter grade."""
    for threshold, grade in GRADE_MAP:
        if score_100 >= threshold:
            return grade
    return "F"


# ---------------------
# Model class (must match training)
# ---------------------
class BertEssayScorer(nn.Module):
    """
    BERT + regression head for essay scoring.
    Uses [CLS] token -> dropout -> linear -> sigmoid for [0, 1] output.
    """
    def __init__(self, model_name="bert-base-uncased", dropout=0.3):
        super().__init__()
        self.bert = BertModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout)
        self.regressor = nn.Linear(self.bert.config.hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :]
        cls_output = self.dropout(cls_output)
        logits = self.regressor(cls_output).squeeze(-1)
        return self.sigmoid(logits)


# ---------------------
# Singleton scorer
# ---------------------
class EssayScorerService:
    """
    Singleton that loads the BERT model once at startup and provides
    scoring methods.
    """
    _instance = None

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self._loaded = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self, checkpoint_path: str, model_name: str = "bert-base-uncased"):
        """Load model and tokenizer."""
        if self._loaded:
            return

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[Scorer] Loading model on {self.device}...")

        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertEssayScorer(model_name)

        # Load checkpoint
        state_dict = torch.load(checkpoint_path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

        self._loaded = True
        print(f"[Scorer] Model loaded successfully from {checkpoint_path}")

    def score_essay(
        self,
        text: str,
        prompt_id: int = 1,
        max_len: int = 512,
        mc_passes: int = 5,
    ) -> dict:
        """
        Score an essay using the BERT model.

        Args:
            text: Essay text
            prompt_id: ASAP prompt ID (1-8), affects denormalization
            max_len: Max token length
            mc_passes: Number of MC dropout forward passes for confidence

        Returns:
            dict with score_normalized, score_100, raw_score, grade, confidence
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)

        # MC Dropout for confidence estimation
        # Run multiple forward passes with dropout enabled
        predictions = []
        self.model.train()  # Enable dropout
        with torch.no_grad():
            for _ in range(mc_passes):
                pred = self.model(input_ids, attention_mask).item()
                predictions.append(pred)
        self.model.eval()

        # Average prediction and confidence
        avg_pred = sum(predictions) / len(predictions)
        std_pred = (sum((p - avg_pred) ** 2 for p in predictions) / len(predictions)) ** 0.5

        # Confidence: higher when std is lower (inverse relationship)
        # Map std to confidence percentage (std of 0 = 100%, std of 0.1+ = ~50%)
        confidence = max(50.0, min(99.0, 100.0 - std_pred * 500))

        # Denormalize
        lo, hi = SCORE_RANGES.get(prompt_id, (0, 100))
        raw_score = round(avg_pred * (hi - lo) + lo)
        raw_score = max(lo, min(hi, raw_score))

        # Scale to 0-100
        score_100 = round(avg_pred * 100, 1)
        score_100 = max(0, min(100, score_100))

        grade = score_to_grade(score_100)

        return {
            "score_normalized": round(avg_pred, 4),
            "score_100": score_100,
            "raw_score": raw_score,
            "raw_score_range": [lo, hi],
            "grade": grade,
            "confidence": round(confidence, 1),
            "prompt_id": prompt_id,
        }
