"""
lang_detector.py — Language Detection for AES Pipeline
=======================================================
Detects whether an essay is English, Kannada, or Code-Mixed.
Uses Unicode range detection (fast, no GPU needed) + optional
langdetect fallback for edge cases.

Usage:
    from lang_detector import detect_language

    detect_language("This is an English essay.")          # → "english"
    detect_language("ಕನ್ನಡ ಪ್ರಬಂಧ ಇಲ್ಲಿದೆ")               # → "kannada"
    detect_language("This essay has ಕನ್ನಡ words mixed in") # → "code_mixed"

Run standalone: python lang_detector.py
"""

import re

# =========================
# 🔹 UNICODE RANGES
# =========================
# Kannada Unicode block: U+0C80 – U+0CFF
KANNADA_PATTERN = re.compile(r'[\u0C80-\u0CFF]')
LATIN_PATTERN = re.compile(r'[a-zA-Z]')

# =========================
# 🔹 CORE DETECTOR
# =========================
def detect_language(text: str) -> str:
    """
    Detect language of the given text.
    
    Returns:
        "kannada"    — majority Kannada script
        "english"    — majority Latin script
        "code_mixed" — significant mix of both
        "unknown"    — too short or unclassifiable
    """
    text = str(text).strip()
    
    if len(text) < 5:
        return "unknown"
    
    # Count script characters (ignoring digits, punctuation, spaces)
    kannada_chars = len(KANNADA_PATTERN.findall(text))
    latin_chars = len(LATIN_PATTERN.findall(text))
    total_script = kannada_chars + latin_chars
    
    if total_script == 0:
        return "unknown"
    
    kannada_ratio = kannada_chars / total_script
    latin_ratio = latin_chars / total_script
    
    # Classification thresholds
    if kannada_ratio > 0.7:
        return "kannada"
    elif latin_ratio > 0.7:
        return "english"
    elif kannada_ratio > 0.2 and latin_ratio > 0.2:
        return "code_mixed"
    elif kannada_ratio > latin_ratio:
        return "kannada"
    else:
        return "english"


def detect_language_batch(texts: list) -> list:
    """Detect language for a list of texts."""
    return [detect_language(t) for t in texts]


# =========================
# 🔹 STANDALONE TEST
# =========================
if __name__ == "__main__":
    test_cases = [
        ("This is a standard English essay about computers.", "english"),
        ("ಕಂಪ್ಯೂಟರ್ ಜನರ ಮೇಲೆ ಧನಾತ್ಮಕ ಪರಿಣಾಮ ಬೀರುತ್ತದೆ", "kannada"),
        ("Computers are ಕಂಪ್ಯೂಟರ್ good for ಜನರ people", "code_mixed"),
        ("Hi", "unknown"),
        ("", "unknown"),
        ("12345!@#$%", "unknown"),
    ]
    
    print("=" * 60)
    print("Language Detector — Self-Test")
    print("=" * 60)
    
    all_pass = True
    for text, expected in test_cases:
        result = detect_language(text)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_pass = False
        print(f"  {status} '{text[:50]}...' → {result} (expected: {expected})")
    
    print("=" * 60)
    if all_pass:
        print("All tests passed! ✅")
    else:
        print("Some tests failed! ❌")
    
    # Demo with a CSV if available
    try:
        import pandas as pd
        print("\n📊 Testing on asap_kannada_test_normalized.csv...")
        df = pd.read_csv("asap_kannada_test_normalized.csv")
        
        # Detect language of Kannada essays
        df['kan_lang'] = df['kannada_essay'].apply(detect_language)
        print(f"  Kannada essay language distribution:")
        print(f"  {df['kan_lang'].value_counts().to_dict()}")
        
        # Detect language of English essays
        df['eng_lang'] = df['essay'].apply(detect_language)
        print(f"  English essay language distribution:")
        print(f"  {df['eng_lang'].value_counts().to_dict()}")
        
    except FileNotFoundError:
        print("\n(No CSV found — skipping CSV demo)")
    except Exception as e:
        print(f"\n⚠️ CSV demo error: {e}")
