"""
bert_scorer.py — BERT Fine-Tuning for Automated Essay Scoring
==============================================================
Fine-tunes bert-base-uncased on the ASAP dataset (all 8 prompts,
multi-task style) with Quadratic Weighted Kappa (QWK) evaluation.

Designed to run as-is on Kaggle (free T4/P100 GPU).

Usage:
    python bert_scorer.py                         # train from scratch
    python bert_scorer.py --eval_only             # evaluate saved model
    python bert_scorer.py --prompt 1              # train on prompt 1 only
    python bert_scorer.py --epochs 5 --lr 2e-5    # custom hyperparams

Requirements:
    pip install torch transformers pandas scikit-learn tqdm
"""

import os
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertModel, get_linear_schedule_with_warmup
from sklearn.model_selection import train_test_split
from sklearn.metrics import cohen_kappa_score
from tqdm import tqdm

# =========================
# 🔹 CONFIG
# =========================
DEFAULT_CONFIG = {
    "data_path": "asap_english_clean.csv",
    "model_name": "bert-base-uncased",
    "max_len": 512,
    "batch_size": 16,
    "epochs": 4,
    "lr": 2e-5,
    "weight_decay": 0.01,
    "warmup_ratio": 0.1,
    "seed": 42,
    "save_dir": "checkpoints",
}

# =========================
# 🔹 SEED
# =========================
def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# =========================
# 🔹 DATASET
# =========================
class EssayDataset(Dataset):
    """
    Tokenizes essays and returns (input_ids, attention_mask, score, prompt_id).
    Re-usable for MuRIL fine-tuning — just swap the tokenizer + model.
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
        encoding = self.tokenizer(
            self.texts[idx],
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'score': torch.tensor(self.scores[idx], dtype=torch.float),
            'prompt_id': torch.tensor(self.prompt_ids[idx], dtype=torch.long),
        }


# =========================
# 🔹 MODEL
# =========================
class BertEssayScorer(nn.Module):
    """
    BERT + regression head for essay scoring.
    Uses [CLS] token → dropout → linear → sigmoid for [0, 1] output.
    """
    def __init__(self, model_name, dropout=0.3):
        super().__init__()
        self.bert = BertModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout)
        self.regressor = nn.Linear(self.bert.config.hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        cls_output = self.dropout(cls_output)
        logits = self.regressor(cls_output).squeeze(-1)
        return self.sigmoid(logits)


# =========================
# 🔹 QWK METRIC
# =========================
SCORE_RANGES = {
    1: (2, 12), 2: (1, 6), 3: (0, 3), 4: (0, 3),
    5: (0, 4),  6: (0, 4), 7: (0, 30), 8: (0, 60),
}

def compute_qwk(preds, targets, prompt_ids):
    """
    Compute per-prompt QWK by denormalizing predictions back to integer scores.
    Returns dict of per-prompt QWK + overall weighted average.
    """
    results = {}
    all_pred_int = []
    all_true_int = []

    for pid in sorted(set(prompt_ids)):
        mask = [i for i, p in enumerate(prompt_ids) if p == pid]
        if len(mask) < 2:
            continue

        lo, hi = SCORE_RANGES[pid]

        # Denormalize to integer scores
        pred_int = [int(round(preds[i] * (hi - lo) + lo)) for i in mask]
        true_int = [int(round(targets[i] * (hi - lo) + lo)) for i in mask]

        # Clip to valid range
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
# 🔹 TRAINING
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

        # Gradient clipping
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

    return avg_loss, qwk, all_preds, all_targets, all_prompts


# =========================
# 🔹 MAIN
# =========================
def main():
    parser = argparse.ArgumentParser(description="BERT Essay Scorer")
    parser.add_argument("--data", default=DEFAULT_CONFIG["data_path"])
    parser.add_argument("--prompt", type=int, default=None,
                        help="Train on single prompt (1-8). Default: all prompts.")
    parser.add_argument("--epochs", type=int, default=DEFAULT_CONFIG["epochs"])
    parser.add_argument("--lr", type=float, default=DEFAULT_CONFIG["lr"])
    parser.add_argument("--batch_size", type=int, default=DEFAULT_CONFIG["batch_size"])
    parser.add_argument("--max_len", type=int, default=DEFAULT_CONFIG["max_len"])
    parser.add_argument("--eval_only", action="store_true")
    parser.add_argument("--checkpoint", default=None,
                        help="Path to a saved checkpoint for eval_only or resume.")
    args = parser.parse_args()

    set_seed(DEFAULT_CONFIG["seed"])

    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🖥️  Device: {device}")
    if device.type == "cuda":
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")

    # ---- Load Data ----
    print(f"\n📂 Loading data from {args.data}...")
    df = pd.read_csv(args.data)

    if args.prompt:
        df = df[df['essay_set'] == args.prompt].reset_index(drop=True)
        print(f"   Filtered to prompt {args.prompt}: {len(df)} essays")
    else:
        print(f"   All prompts: {len(df)} essays")

    # Train/val split (stratified by prompt)
    train_df, val_df = train_test_split(
        df, test_size=0.15, random_state=DEFAULT_CONFIG["seed"],
        stratify=df['essay_set']
    )
    print(f"   Train: {len(train_df)} | Val: {len(val_df)}")

    # ---- Tokenizer ----
    print(f"\n🔤 Loading tokenizer: {DEFAULT_CONFIG['model_name']}...")
    tokenizer = BertTokenizer.from_pretrained(DEFAULT_CONFIG["model_name"])

    train_dataset = EssayDataset(
        texts=train_df['essay'].tolist(),
        scores=train_df['normalized_score'].tolist(),
        prompt_ids=train_df['essay_set'].tolist(),
        tokenizer=tokenizer,
        max_len=args.max_len
    )
    val_dataset = EssayDataset(
        texts=val_df['essay'].tolist(),
        scores=val_df['normalized_score'].tolist(),
        prompt_ids=val_df['essay_set'].tolist(),
        tokenizer=tokenizer,
        max_len=args.max_len
    )

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size)

    # ---- Model ----
    print(f"\n🧠 Building model...")
    model = BertEssayScorer(DEFAULT_CONFIG["model_name"]).to(device)

    if args.checkpoint and os.path.exists(args.checkpoint):
        print(f"   Loading checkpoint: {args.checkpoint}")
        model.load_state_dict(torch.load(args.checkpoint, map_location=device))

    if args.eval_only:
        print("\n📊 Eval-only mode")
        val_loss, qwk, _, _, _ = evaluate(model, val_loader, device)
        print(f"   Val Loss: {val_loss:.4f}")
        print(f"   QWK scores: {qwk}")
        return

    # ---- Optimizer + Scheduler ----
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

    # ---- Training Loop ----
    os.makedirs(DEFAULT_CONFIG["save_dir"], exist_ok=True)
    best_qwk = -1
    best_epoch = -1

    print(f"\n🚀 Training for {args.epochs} epochs...")
    print(f"   LR: {args.lr} | Batch: {args.batch_size} | Max Len: {args.max_len}")
    print(f"   Total steps: {total_steps} | Warmup: {warmup_steps}")
    print("=" * 70)

    for epoch in range(1, args.epochs + 1):
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, scheduler, device)

        # Evaluate
        val_loss, qwk, _, _, _ = evaluate(model, val_loader, device)

        overall_qwk = qwk.get("overall", 0)

        print(f"\n📈 Epoch {epoch}/{args.epochs}")
        print(f"   Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
        print(f"   QWK: {qwk}")

        # Save best model
        if overall_qwk > best_qwk:
            best_qwk = overall_qwk
            best_epoch = epoch

            prompt_tag = f"prompt{args.prompt}" if args.prompt else "all_prompts"
            save_path = os.path.join(
                DEFAULT_CONFIG["save_dir"],
                f"bert_{prompt_tag}_best.pt"
            )
            torch.save(model.state_dict(), save_path)
            print(f"   💾 New best! Saved to {save_path}")

    print("\n" + "=" * 70)
    print(f"✅ Training complete!")
    print(f"   Best QWK: {best_qwk:.4f} (epoch {best_epoch})")
    print(f"   Checkpoint: {DEFAULT_CONFIG['save_dir']}/bert_*_best.pt")

    # ---- Smoke Test ----
    print("\n🔬 Smoke test — scoring 5 sample essays from validation set...")
    model.eval()
    samples = val_df.head(5)

    with torch.no_grad():
        for _, row in samples.iterrows():
            encoding = tokenizer(
                row['essay'],
                max_length=args.max_len,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )
            input_ids = encoding['input_ids'].to(device)
            attention_mask = encoding['attention_mask'].to(device)

            pred = model(input_ids, attention_mask).item()

            lo, hi = SCORE_RANGES[row['essay_set']]
            raw_pred = round(pred * (hi - lo) + lo)

            print(
                f"   Prompt {row['essay_set']} | "
                f"True: {row['domain1_score']:.0f} | "
                f"Pred: {raw_pred} (norm: {pred:.3f}) | "
                f"Essay: {row['essay'][:80]}..."
            )


if __name__ == "__main__":
    main()
