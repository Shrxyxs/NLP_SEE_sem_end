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
class MurilEssayScorer(nn.Module):
    """
    MuRIL + regression head for Kannada essay scoring.
    """
    def __init__(self, model_name="google/muril-base-cased", dropout=0.3):
        super().__init__()
        from transformers import AutoModel
        self.muril = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout)
        self.regressor = nn.Linear(self.muril.config.hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, input_ids, attention_mask):
        outputs = self.muril(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :]
        cls_output = self.dropout(cls_output)
        logits = self.regressor(cls_output).squeeze(-1)
        return self.sigmoid(logits)


# ---------------------
# Singleton scorer
# ---------------------
class EssayScorerService:
    """
    Singleton that loads BERT (English) and MuRIL (Kannada) models 
    to provide bilingual essay scoring.
    """
    _instance = None

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # English model state
        self.en_model = None
        self.en_tokenizer = None
        self.en_loaded = False
        self.en_checkpoint = None

        # Kannada model state
        self.kn_model = None
        self.kn_tokenizer = None
        self.kn_loaded = False
        self.kn_checkpoint = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def _loaded(self) -> bool:
        return self.en_loaded or self.kn_loaded

    def load(self, checkpoint_path: str, model_name: str = "bert-base-uncased"):
        """Save path and load English model at startup."""
        self.en_checkpoint = checkpoint_path
        self._load_english(model_name)

    def _load_english(self, model_name: str = "bert-base-uncased"):
        if self.en_loaded:
            return True
        if not self.en_checkpoint or not os.path.exists(self.en_checkpoint):
            print(f"[Scorer] English checkpoint not found at {self.en_checkpoint}")
            return False

        print(f"[Scorer] Loading English model ({model_name}) on {self.device}...")
        self.en_tokenizer = BertTokenizer.from_pretrained(model_name)
        self.en_model = BertEssayScorer(model_name)

        # Load checkpoint weights
        state_dict = torch.load(self.en_checkpoint, map_location=self.device, weights_only=True)
        self.en_model.load_state_dict(state_dict)
        self.en_model.to(self.device)
        self.en_model.eval()
        
        self.en_loaded = True
        print(f"[Scorer] English model loaded successfully.")
        return True

    def _load_kannada(self, model_name: str = "google/muril-base-cased"):
        if self.kn_loaded:
            return True

        checkpoint_dir = os.path.dirname(self.en_checkpoint) if self.en_checkpoint else ".."
        self.kn_checkpoint = os.path.join(checkpoint_dir, "muril_all_prompts_best.pt")

        if not os.path.exists(self.kn_checkpoint):
            print(f"[Scorer] Kannada MuRIL checkpoint not found at {self.kn_checkpoint}. Falling back to English.")
            return False

        print(f"[Scorer] Loading Kannada MuRIL model ({model_name}) on {self.device}...")
        from transformers import AutoTokenizer
        self.kn_tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.kn_model = MurilEssayScorer(model_name)

        # Load checkpoint weights
        state_dict = torch.load(self.kn_checkpoint, map_location=self.device, weights_only=True)
        self.kn_model.load_state_dict(state_dict)
        self.kn_model.to(self.device)
        self.kn_model.eval()

        self.kn_loaded = True
        print(f"[Scorer] Kannada MuRIL model loaded successfully.")
        return True

    def score_essay(
        self,
        text: str,
        prompt_id: int = 1,
        max_len: int = 512,
        mc_passes: int = 5,
        language: str = "english",
    ) -> dict:
        """
        Score an essay using the appropriate BERT (English) or MuRIL (Kannada) model.
        """
        use_kannada = False
        if language in ["kannada", "code_mixed"]:
            if self._load_kannada():
                use_kannada = True

        if use_kannada:
            model = self.kn_model
            tokenizer = self.kn_tokenizer
            print("[Scorer] Evaluating Kannada essay using MuRIL Scorer...")
        else:
            self._load_english()
            model = self.en_model
            tokenizer = self.en_tokenizer
            print("[Scorer] Evaluating English/fallback essay using BERT Scorer...")

        if model is None or tokenizer is None:
            raise RuntimeError("Selected scoring model could not be loaded.")

        # Tokenize
        encoding = tokenizer(
            text,
            max_length=max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)

        # MC Dropout for confidence estimation
        predictions = []
        model.train()  # Enable dropout
        with torch.no_grad():
            for _ in range(mc_passes):
                pred = model(input_ids, attention_mask).item()
                predictions.append(pred)
        model.eval()

        # Average prediction and confidence
        avg_pred = sum(predictions) / len(predictions)
        std_pred = (sum((p - avg_pred) ** 2 for p in predictions) / len(predictions)) ** 0.5

        # Confidence bounds [50%, 99%]
        confidence = max(50.0, min(99.0, 100.0 - std_pred * 500))

        # Denormalize score to original prompt rubric range
        lo, hi = SCORE_RANGES.get(prompt_id, (0, 100))
        raw_score = round(avg_pred * (hi - lo) + lo)
        raw_score = max(lo, min(hi, raw_score))

        # Scale score to 0-100%
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
