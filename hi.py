import pandas as pd

# =========================
# 🔹 CONFIG
# =========================
INPUT_PATH = "asap_kannada_prompt1.csv"
OUTPUT_PATH = "asap_kannada_prompt1_normalized.csv"

SCORE_RANGES = {
    1: (2, 12), 2: (1, 6), 3: (0, 3), 4: (0, 3),
    5: (0, 4), 6: (0, 4), 7: (0, 30), 8: (0, 60)
}

# =========================
# 🔹 LOAD
# =========================
df = pd.read_csv(INPUT_PATH)

# =========================
# 🔹 NORMALIZE
# =========================
def normalize(row):
    lo, hi = SCORE_RANGES[row['essay_set']]
    return (row['domain1_score'] - lo) / (hi - lo)

df['normalized_score'] = df.apply(normalize, axis=1)

# =========================
# 🔹 OPTIONAL CLEAN (recommended)
# Keep only rows that actually contain Kannada
# =========================
import re
kannada_range = re.compile(r'[\u0C80-\u0CFF]')

df = df[df['kannada_essay'].apply(lambda x: bool(kannada_range.search(str(x))))]

# =========================
# 🔹 SAVE
# =========================
df.to_csv(OUTPUT_PATH, index=False)

print("Saved:", OUTPUT_PATH)
print("Shape:", df.shape)
print("Score range:", df['normalized_score'].min(), df['normalized_score'].max())