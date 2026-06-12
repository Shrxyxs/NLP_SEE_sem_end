"""
train_muril.py — MuRIL Fine-Tuning for Kannada Automated Essay Scoring (AES)
=============================================================================
Fine-tunes the Google MuRIL (Multilingual Representations for Indian Languages)
model on translated Kannada essays (from asap_kannada_full.csv) for grading.

Requirements:
    pip install torch transformers pandas scikit-learn tqdm

Usage:
    python train_muril.py --data asap_kannada_full.csv --epochs 5 --lr 3e-5
"""

import os
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from sklearn.model_selection import train_test_split
from sklearn.metrics import cohen_kappa_score
from tqdm import tqdm

# =========================
# 🔹 CONFIG & SCORE RANGES
# =========================
DEFAULT_CONFIG = {
    "model_name": "google/muril-base-cased",
    "max_len": 512,
    "batch_size": 16,
    "epochs": 5,
    "lr": 3e-5,
    "weight_decay": 0.01,
    "warmup_ratio": 0.1,
    "seed": 42,
    "save_dir": "checkpoints_muril",
}

SCORE_RANGES = {
    1: (2, 12), 2: (1, 6), 3: (0, 3), 4: (0, 3),
    5: (0, 4),  6: (0, 4), 7: (0, 30), 8: (0, 60),
}

# =========================
# 🔹 UTILS
# =========================
def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def normalize_score(score, essay_set):
    lo, hi = SCORE_RANGES.get(essay_set, (0, 100))
    return (score - lo) / (hi - lo)

# =========================
# 🔹 DATASET CLASS
# =========================
class KannadaEssayDataset(Dataset):
    """
    Loads Kannada essays, tokenizes them using MuRIL tokenizer, 
    and returns (input_ids, attention_mask, normalized_score, prompt_id).
    """
    def __init__(self, texts, scores, prompt_ids, tokenizer, max_len):
        self.texts = texts
        self.scores = scores
        self.prompt_ids = prompt_ids
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        # Handle potential non-string values gracefully
        text = str(self.texts[idx])
        encoding = self.tokenizer(
            text,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        # Calculate normalized score on the fly
        pid = int(self.prompt_ids[idx])
        raw_score = float(self.scores[idx])
        norm_score = normalize_score(raw_score, pid)

        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'score': torch.tensor(norm_score, dtype=torch.float),
            'prompt_id': torch.tensor(pid, dtype=torch.long),
        }

# =========================
# 🔹 MuRIL SCORER MODEL
# =========================
class MurilEssayScorer(nn.Module):
    """
    MuRIL + Regression Head.
    Extracts the pooler output (or CLS token) from MuRIL, applies dropout,
    and runs a linear regression layer with Sigmoid to output normalized scores [0, 1].
    """
    def __init__(self, model_name="google/muril-base-cased", dropout=0.3):
        super().__init__()
        self.muril = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout)
        self.regressor = nn.Linear(self.muril.config.hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, input_ids, attention_mask):
        outputs = self.muril(input_ids=input_ids, attention_mask=attention_mask)
        # Use pooler output (CLS token representation with an extra linear + tanh layer)
        # or use outputs.last_hidden_state[:, 0, :] directly.
        cls_output = outputs.last_hidden_state[:, 0, :]
        cls_output = self.dropout(cls_output)
        logits = self.regressor(cls_output).squeeze(-1)
        return self.sigmoid(logits)

# =========================
# 🔹 METRIC COMPUTATION (QWK)
# =========================
def compute_qwk(preds, targets, prompt_ids):
    """
    Denormalize predictions back to prompt-specific integer ranges
    and calculate Quadratic Weighted Kappa (QWK) for each prompt and overall.
    """
    results = {}
    all_pred_int = []
    all_true_int = []

    for pid in sorted(set(prompt_ids)):
        mask = [i for i, p in enumerate(prompt_ids) if p == pid]
        if len(mask) < 2:
            continue

        lo, hi = SCORE_RANGES[pid]

        # Denormalize to original integer ranges
        pred_int = [int(round(preds[i] * (hi - lo) + lo)) for i in mask]
        true_int = [int(round(targets[i] * (hi - lo) + lo)) for i in mask]

        # Clip predictions to allowable score bounds
        pred_int = [max(lo, min(hi, p)) for p in pred_int]
        true_int = [max(lo, min(hi, t)) for t in true_int]

        qwk = cohen_kappa_score(true_int, pred_int, weights='quadratic')
        results[f"prompt_{pid}"] = round(qwk, 4)

        all_pred_int.extend(pred_int)
        all_true_int.extend(true_int)

    if all_pred_int:
        overall = cohen_kappa_score(all_true_int, all_pred_int, weights='quadratic')
        results["overall"] = round(overall, 4)

    return results

# =========================
# 🔹 TRAINING & VALIDATION
# =========================
def train_epoch(model, loader, optimizer, scheduler, device):
    model.train()
    total_loss = 0
    criterion = nn.MSELoss()

    for batch in tqdm(loader, desc="Training", leave=False):
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        scores = batch['score'].to(device)

        optimizer.zero_grad()
        preds = model(input_ids, attention_mask)
        loss = criterion(preds, scores)
        loss.backward()

        # Gradient clipping to prevent exploding gradients
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        optimizer.step()
        scheduler.step()

        total_loss += loss.item()

    return total_loss / len(loader)

def evaluate(model, loader, device):
    model.eval()
    all_preds = []
    all_targets = []
    all_prompts = []
    total_loss = 0
    criterion = nn.MSELoss()

    with torch.no_grad():
        for batch in tqdm(loader, desc="Evaluating", leave=False):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            scores = batch['score'].to(device)
            prompt_ids = batch['prompt_id']

            preds = model(input_ids, attention_mask)
            loss = criterion(preds, scores)
            total_loss += loss.item()

            all_preds.extend(preds.cpu().numpy().tolist())
            all_targets.extend(scores.cpu().numpy().tolist())
            all_prompts.extend(prompt_ids.numpy().tolist())

    avg_loss = total_loss / len(loader)
    qwk = compute_qwk(all_preds, all_targets, all_prompts)

    return avg_loss, qwk

# =========================
# 🔹 MAIN EXECUTION
# =========================
def main():
    parser = argparse.ArgumentParser(description="MuRIL Essay Scorer for Kannada")
    parser.add_argument("--data", default="asap_kannada_full.csv", help="Path to Kannada essays dataset")
    parser.add_argument("--epochs", type=int, default=DEFAULT_CONFIG["epochs"])
    parser.add_argument("--lr", type=float, default=DEFAULT_CONFIG["lr"])
    parser.add_argument("--batch_size", type=int, default=DEFAULT_CONFIG["batch_size"])
    parser.add_argument("--max_len", type=int, default=DEFAULT_CONFIG["max_len"])
    parser.add_argument("--prompt", type=int, default=None, help="Train on single prompt (1-8)")
    args = parser.parse_args()

    set_seed(DEFAULT_CONFIG["seed"])

    # Device Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🖥️ Device detected: {device}")
    if device.type == "cuda":
        print(f"   GPU Model: {torch.cuda.get_device_name(0)}")

    # Load Dataset
    if not os.path.exists(args.data):
        raise FileNotFoundError(f"Dataset path '{args.data}' does not exist!")

    print(f"\n📂 Loading dataset from {args.data}...")
    df = pd.read_csv(args.data)
    
    # Drop rows missing critical columns
    df = df.dropna(subset=["kannada_essay", "domain1_score", "essay_set"]).reset_index(drop=True)

    if args.prompt:
        df = df[df['essay_set'] == args.prompt].reset_index(drop=True)
        print(f"   Filtered to prompt {args.prompt}: {len(df)} essays")
    else:
        print(f"   Full multi-prompt training: {len(df)} essays")

    # Train/Validation Split (85% Train, 15% Validation)
    train_df, val_df = train_test_split(
        df, test_size=0.15, random_state=DEFAULT_CONFIG["seed"],
        stratify=df['essay_set'] if not args.prompt else None
    )
    print(f"   Training Set Size: {len(train_df)} | Validation Set Size: {len(val_df)}")

    # Load MuRIL Tokenizer
    print(f"\n🔤 Loading MuRIL tokenizer ({DEFAULT_CONFIG['model_name']})...")
    tokenizer = AutoTokenizer.from_pretrained(DEFAULT_CONFIG["model_name"])

    # Datasets & Dataloaders
    train_dataset = KannadaEssayDataset(
        texts=train_df['kannada_essay'].tolist(),
        scores=train_df['domain1_score'].tolist(),
        prompt_ids=train_df['essay_set'].tolist(),
        tokenizer=tokenizer,
        max_len=args.max_len
    )
    val_dataset = KannadaEssayDataset(
        texts=val_df['kannada_essay'].tolist(),
        scores=val_df['domain1_score'].tolist(),
        prompt_ids=val_df['essay_set'].tolist(),
        tokenizer=tokenizer,
        max_len=args.max_len
    )

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size)

    # Instantiate MuRIL Regressor
    print(f"\n🧠 Instantiating MuRIL Scorer...")
    model = MurilEssayScorer(DEFAULT_CONFIG["model_name"]).to(device)

    # Optimizer & Scheduler Setup
    total_steps = len(train_loader) * args.epochs
    warmup_steps = int(total_steps * DEFAULT_CONFIG["warmup_ratio"])

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=DEFAULT_CONFIG["weight_decay"]
    )
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps
    )

    # Save Checkpoint Directory
    os.makedirs(DEFAULT_CONFIG["save_dir"], exist_ok=True)
    best_qwk = -1
    best_epoch = -1

    # Training Loop
    print(f"\n🚀 Starting training for {args.epochs} epochs...")
    print(f"   Learning Rate: {args.lr} | Batch Size: {args.batch_size} | Max Sequence Length: {args.max_len}")
    print("=" * 75)

    for epoch in range(1, args.epochs + 1):
        # Training Phase
        train_loss = train_epoch(model, train_loader, optimizer, scheduler, device)

        # Validation Phase
        val_loss, qwk = evaluate(model, val_loader, device)
        overall_qwk = qwk.get("overall", 0)

        print(f"\n📈 Epoch {epoch}/{args.epochs}")
        print(f"   Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
        print(f"   Per-Prompt QWK: {qwk}")

        # Save Checkpoint if QWK improves
        if overall_qwk > best_qwk:
            best_qwk = overall_qwk
            best_epoch = epoch
            
            prompt_tag = f"prompt{args.prompt}" if args.prompt else "all_prompts"
            save_path = os.path.join(
                DEFAULT_CONFIG["save_dir"],
                f"muril_{prompt_tag}_best.pt"
            )
            torch.save(model.state_dict(), save_path)
            print(f"   💾 Saved new best checkpoint to {save_path}")

    print("\n" + "=" * 75)
    print(f"✅ Training completed successfully!")
    print(f"   Best Overall QWK: {best_qwk:.4f} (attained on Epoch {best_epoch})")
    print(f"   Saved Checkpoint Location: {DEFAULT_CONFIG['save_dir']}/muril_*_best.pt")

if __name__ == "__main__":
    main()
