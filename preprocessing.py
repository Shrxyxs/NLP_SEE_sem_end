"""
preprocessing.py — ASAP English Data Prep
==========================================
Loads training_set_rel3.tsv, cleans essays, normalizes scores to [0,1],
and saves asap_english_clean.csv ready for BERT fine-tuning.

Run: python preprocessing.py
"""

import re
import pandas as pd

# =========================
# 🔹 CONFIG
# =========================
INPUT_PATH = "training_set_rel3.tsv"
OUTPUT_PATH = "asap_english_clean.csv"

# Official ASAP score ranges per prompt (min, max)
SCORE_RANGES = {
    1: (2, 12),
    2: (1, 6),
    3: (0, 3),
    4: (0, 3),
    5: (0, 4),
    6: (0, 4),
    7: (0, 30),
    8: (0, 60),
}

# =========================
# 🔹 TEXT CLEANING
# =========================
def clean_text(text):
    """Remove HTML tags, normalize whitespace, keep @PROPER_NOUN markers."""
    text = str(text)
    text = re.sub(r'<[^>]+>', '', text)           # strip HTML
    text = re.sub(r'@\w+', '@PROPER_NOUN', text)  # anonymize mentions
    text = re.sub(r'\s+', ' ', text).strip()       # collapse whitespace
    return text

# =========================
# 🔹 SCORE NORMALIZATION
# =========================
def normalize_score(row):
    """Normalize domain1_score to [0, 1] using the prompt's official range."""
    lo, hi = SCORE_RANGES[row['essay_set']]
    return (row['domain1_score'] - lo) / (hi - lo)

# =========================
# 🔹 MAIN
# =========================
def main():
    print("Loading dataset...")
    df = pd.read_csv(INPUT_PATH, sep='\t', encoding='latin1')

    # Keep only the columns we need
    required_cols = ['essay_id', 'essay_set', 'essay', 'domain1_score']
    df = df[required_cols].dropna()

    print(f"  Raw essays: {len(df)}")

    # Clean text
    print("Cleaning text...")
    df['essay'] = df['essay'].apply(clean_text)

    # Drop any essays that are empty after cleaning
    df = df[df['essay'].str.len() > 10].copy()
    print(f"  After cleaning: {len(df)}")

    # Normalize scores
    print("Normalizing scores...")
    df['normalized_score'] = df.apply(normalize_score, axis=1)

    # Sanity checks
    assert df['normalized_score'].min() >= 0.0, "Score below 0 found!"
    assert df['normalized_score'].max() <= 1.0, "Score above 1 found!"

    # Summary per prompt
    print("\n--- Per-prompt summary ---")
    for prompt_id in sorted(df['essay_set'].unique()):
        subset = df[df['essay_set'] == prompt_id]
        lo, hi = SCORE_RANGES[prompt_id]
        print(
            f"  Prompt {prompt_id}: {len(subset):>5} essays | "
            f"raw score [{lo}–{hi}] | "
            f"normalized [{subset['normalized_score'].min():.2f}–{subset['normalized_score'].max():.2f}] | "
            f"mean {subset['normalized_score'].mean():.3f}"
        )

    # Save
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n[OK] Saved {len(df)} essays to {OUTPUT_PATH}")
    print(f"   Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()
