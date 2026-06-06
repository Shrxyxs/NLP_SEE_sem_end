import pandas as pd
from tqdm import tqdm
import torch
import re
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from huggingface_hub import login

login("use hugging face code")

# =========================
# 🔹 CONFIG
# =========================
INPUT_PATH = "training_set_rel3.tsv"
OUTPUT_PATH = "asap_kannada_full.csv"

BATCH_SIZE = 32   # 🔥 BIG speedup
MAX_INPUT_LEN = 1024
MAX_OUTPUT_LEN = 1024

# =========================
# 🔹 CLEANING
# =========================
def clean_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'@\w+', '@PROPER_NOUN', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# =========================
# 🔹 LOAD DATA
# =========================
print("Loading dataset...")
df = pd.read_csv(INPUT_PATH, sep='\t', encoding='latin1')

df = df[['essay_id', 'essay_set', 'essay', 'domain1_score']].dropna()
df['essay'] = df['essay'].apply(clean_text)

subset = df.reset_index(drop=True)

print(f"Loaded {len(subset)} essays")

# =========================
# 🔹 LOAD MODEL (NLLB — optimized)
# =========================
print("Loading model...")

model_name = "facebook/nllb-200-distilled-600M"

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.src_lang = "eng_Latn"

model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# 🔥 HALF PRECISION = MASSIVE SPEED BOOST
if device.type == "cuda":
    model = model.half()

print(f"Using device: {device}")

# =========================
# 🔹 TRANSLATION
# =========================
def translate_batch(essays):
    translated = []

    total_batches = (len(essays) + BATCH_SIZE - 1) // BATCH_SIZE

    with tqdm(total=total_batches, desc="Translating", unit="batch") as pbar:
        for i in range(0, len(essays), BATCH_SIZE):
            batch = essays[i:i+BATCH_SIZE]

            try:
                inputs = tokenizer(
                    batch,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=MAX_INPUT_LEN
                )

                inputs = {k: v.to(device) for k, v in inputs.items()}

                with torch.no_grad():  # 🔥 IMPORTANT
                    outputs = model.generate(
                        **inputs,
                        forced_bos_token_id=tokenizer.lang_code_to_id["kan_Knda"],
                        max_length=MAX_OUTPUT_LEN,
                        num_beams=1
                    )

                decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
                translated.extend(decoded)

            except Exception as e:
                print(f"\n❌ Error at batch {i}: {e}")
                translated.extend(batch)

            pbar.update(1)

    return translated


# =========================
# 🔹 RUN TRANSLATION
# =========================
print("Translating essays...")

subset['kannada_essay'] = translate_batch(
    subset['essay'].tolist()
)

# =========================
# 🔹 SAVE
# =========================
subset.to_csv(OUTPUT_PATH, index=False)

print(f"Saved to {OUTPUT_PATH}")