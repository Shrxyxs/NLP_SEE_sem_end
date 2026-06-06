from transformers import AutoTokenizer
import pandas as pd

# =====================
# CONFIG
# =====================
FILE_PATH = "asap_kannada_full.csv"      # change this
TEXT_COLUMN = "essay"           # change if needed

MODEL_NAME = "facebook/nllb-200-distilled-600M"

# =====================
# LOAD
# =====================
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print("Loading dataset...")

if FILE_PATH.endswith(".tsv"):
    df = pd.read_csv(FILE_PATH, sep="\t")
else:
    df = pd.read_csv(FILE_PATH)

texts = df[TEXT_COLUMN].dropna().astype(str).tolist()

print(f"Found {len(texts)} essays")

# =====================
# TOKEN LENGTH ANALYSIS
# =====================
lengths = []

for text in texts:
    lengths.append(len(tokenizer.encode(text)))

print("\n===== RESULTS =====")
print("Min length:", min(lengths))
print("Average length:", round(sum(lengths)/len(lengths), 2))
print("Max length:", max(lengths))

for limit in [128, 256, 512, 1024]:
    count = sum(x > limit for x in lengths)
    percent = 100 * count / len(lengths)

    print(
        f"Over {limit}: {count} essays "
        f"({percent:.2f}%)"
    )

# =====================
# LONGEST ESSAYS
# =====================
print("\nTop 10 longest essays:")

sorted_lengths = sorted(lengths, reverse=True)

for i in range(min(10, len(sorted_lengths))):
    print(f"{i+1}. {sorted_lengths[i]} tokens")