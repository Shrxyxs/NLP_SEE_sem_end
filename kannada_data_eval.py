import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from huggingface_hub import login

login("use hugging face code")

# =========================
# 🔹 CONFIG
# =========================
INPUT_PATH = "asap_kannada_full.csv"
OUTPUT_PATH = "asap_kannada_evaluated.csv"
BATCH_SIZE = 8

# =========================
# 🔹 LOAD DATA
# =========================
df = pd.read_csv(INPUT_PATH)
df = df.dropna(subset=["essay", "kannada_essay"]).reset_index(drop=True)

print(f"Loaded {len(df)} samples")

# =========================
# 🔹 DEVICE
# =========================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# =========================
# 🔹 BACK TRANSLATION MODEL (FIXED)
# =========================
print("Loading back-translation model...")

model_name = "Helsinki-NLP/opus-mt-mul-en"

tokenizer_bt = AutoTokenizer.from_pretrained(model_name)
model_bt = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)

# =========================
# 🔹 EMBEDDING MODEL
# =========================
print("Loading embedding model...")

embed_model = SentenceTransformer(
    'all-MiniLM-L6-v2',
    device="cuda" if torch.cuda.is_available() else "cpu"
)

# =========================
# 🔹 FUNCTIONS
# =========================
def back_translate_batch(texts):
    inputs = tokenizer_bt(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    outputs = model_bt.generate(
        **inputs,
        max_length=256,
        num_beams=1
    )

    decoded = tokenizer_bt.batch_decode(outputs, skip_special_tokens=True)

    # 🔥 safeguard against empty outputs
    decoded = [d if d.strip() != "" else "[EMPTY]" for d in decoded]

    return decoded


def compute_similarity(orig_list, back_list):
    emb1 = embed_model.encode(
        orig_list,
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    emb2 = embed_model.encode(
        back_list,
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    scores = (emb1 * emb2).sum(dim=1)  # cosine similarity
    return scores.cpu().numpy()


# =========================
# 🔹 PROCESS
# =========================
back_translations = []
similarities = []

print("Processing...")

for i in tqdm(range(0, len(df), BATCH_SIZE)):
    batch = df.iloc[i:i+BATCH_SIZE]

    original = batch["essay"].tolist()
    kannada = batch["kannada_essay"].tolist()

    try:
        # Back translate
        back = back_translate_batch(kannada)

        # 🔥 DEBUG ONLY FIRST BATCH
        if i == 0:
            print("\n--- DEBUG SAMPLE ---")
            print("Original:", original[0])
            print("Kannada:", kannada[0])
            print("Back:", back[0])

        # Similarity
        sims = compute_similarity(original, back)

    except Exception as e:
        print(f"Error at batch {i}: {e}")
        back = ["[ERROR]"] * len(batch)
        sims = [0.0] * len(batch)

    back_translations.extend(back)
    similarities.extend(sims)

# =========================
# 🔹 SAVE RESULTS
# =========================
df["back_translated"] = back_translations
df["semantic_similarity"] = similarities

# =========================
# 🔹 QUALITY LABEL
# =========================
def label(score):
    if score > 0.85:
        return "excellent"
    elif score > 0.75:
        return "good"
    elif score > 0.6:
        return "okay"
    else:
        return "poor"

df["quality"] = df["semantic_similarity"].apply(label)

df.to_csv(OUTPUT_PATH, index=False)

print("Saved to", OUTPUT_PATH)

# =========================
# 🔹 SUMMARY
# =========================
print("\nSummary:")
print(df["semantic_similarity"].describe())

print("\nQuality distribution:")
print(df["quality"].value_counts())