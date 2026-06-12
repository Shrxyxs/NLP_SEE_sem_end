"""
analyzer.py - Text Analysis Module
====================================
Provides trait-level essay analysis: content, organization, language use,
conventions (grammar), vocabulary, readability, and writing consistency.
Uses language-tool-python for grammar checking and textstat for readability.
"""

import re
import math
import textstat
import language_tool_python
from collections import Counter

class FallbackMatch:
    def __init__(self, message, context, offset, length, rule_id, replacements, category):
        self.message = message
        self.context = context
        self.offset = offset
        self.errorLength = length
        self.length = length
        self.rule_id = rule_id
        self.replacements = replacements
        self.category = category


class FallbackLanguageTool:
    def __init__(self):
        pass

    def check(self, text: str):
        matches = []
        
        # 1. System warning that we are running in light mode
        matches.append(FallbackMatch(
            message="Notice: Basic conventions check enabled. Install Java on the server to enable detailed grammar & spelling evaluation.",
            context="System environment warning: Java not found.",
            offset=0,
            length=0,
            rule_id="JAVA_MISSING_WARNING",
            replacements=[],
            category="SYSTEM"
        ))

        # 2. Check duplicate words (e.g. "the the", "and and")
        for m in re.finditer(r'\b([a-zA-Z]+)\s+\1\b', text, re.IGNORECASE):
            word = m.group(1)
            matches.append(FallbackMatch(
                message=f"Possible duplicated word: '{word}'",
                context=m.group(0),
                offset=m.start(),
                length=m.end() - m.start(),
                rule_id="DUP_WORD",
                replacements=[word],
                category="TYPOGRAPHY"
            ))

        # 3. Check lack of capitalization after sentence boundary
        for m in re.finditer(r'(?:[.!?]\s+|^)([a-z])', text):
            char_idx = m.start(1)
            char = m.group(1)
            matches.append(FallbackMatch(
                message="This sentence does not start with an uppercase letter.",
                context=text[max(0, char_idx-10):min(len(text), char_idx+10)],
                offset=char_idx,
                length=1,
                rule_id="UPPERCASE_SENTENCE_START",
                replacements=[char.upper()],
                category="CASING"
            ))

        # 4. Check spacing before punctuation (e.g., "hello , world")
        for m in re.finditer(r'\s+([,.!?])', text):
            matches.append(FallbackMatch(
                message="Unnecessary space before punctuation mark.",
                context=m.group(0),
                offset=m.start(),
                length=m.end() - m.start(),
                rule_id="SPACE_BEFORE_PUNCTUATION",
                replacements=[m.group(1)],
                category="TYPOGRAPHY"
            ))

        # 5. Check consecutive punctuation (e.g., "hello,, world")
        for m in re.finditer(r'([,.!?])\1+', text):
            punc = m.group(1)
            matches.append(FallbackMatch(
                message=f"Consecutive punctuation marks: '{m.group(0)}'",
                context=m.group(0),
                offset=m.start(),
                length=m.end() - m.start(),
                rule_id="CONSECUTIVE_PUNCTUATION",
                replacements=[punc],
                category="TYPOGRAPHY"
            ))

        return matches


def _add_java_to_path_if_needed():
    import os
    import shutil
    import sys

    if shutil.which("java") is not None:
        return  # Java is already in PATH

    # Java is not in PATH, search common Windows installation directories
    if sys.platform == "win32":
        common_paths = [
            r"C:\Program Files\Java",
            r"C:\Program Files (x86)\Java",
        ]
        for base in common_paths:
            if os.path.exists(base):
                for item in os.listdir(base):
                    full_path = os.path.join(base, item)
                    if os.path.isdir(full_path):
                        bin_dir = os.path.join(full_path, "bin")
                        java_exe = os.path.join(bin_dir, "java.exe")
                        if os.path.exists(java_exe):
                            print(f"[Analyzer] Found Java at {java_exe}, adding to PATH and setting JAVA_HOME")
                            os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]
                            os.environ["JAVA_HOME"] = full_path
                            return


# ---------------------
# Initialize LanguageTool (downloads ~170MB on first run)
# ---------------------
_tool = None


def _get_language_tool():
    global _tool
    if _tool is None:
        _add_java_to_path_if_needed()
        try:
            print("[Analyzer] Loading LanguageTool (first run may download ~170MB)...")
            _tool = language_tool_python.LanguageTool('en-US')
            print("[Analyzer] LanguageTool ready.")
        except Exception as e:
            print(f"[Analyzer] Failed to load LanguageTool (Java might be missing): {e}")
            print("[Analyzer] Falling back to Regex-based syntax/grammar checker.")
            _tool = FallbackLanguageTool()
    return _tool


# ---------------------
# Transition / discourse markers
# ---------------------
TRANSITION_WORDS = {
    "however", "therefore", "furthermore", "moreover", "additionally",
    "consequently", "nevertheless", "meanwhile", "similarly", "likewise",
    "in contrast", "on the other hand", "for example", "for instance",
    "in conclusion", "in summary", "to summarize", "first", "second",
    "third", "finally", "next", "then", "also", "besides", "thus",
    "hence", "accordingly", "as a result", "in addition", "specifically",
}

# ---------------------
# Common advanced vocabulary
# ---------------------
ADVANCED_WORDS = {
    "acknowledge", "advocate", "alleviate", "ambiguous", "analogy",
    "articulate", "aspiration", "benchmark", "catalyst", "coherent",
    "collaborate", "comprehensive", "consensus", "constitute", "contemplate",
    "contemporary", "contradict", "controversy", "culminate", "deliberate",
    "demonstrate", "deteriorate", "dilemma", "diminish", "discourse",
    "disposition", "disseminate", "distinction", "elaborate", "emphasize",
    "encompass", "endeavor", "enhance", "establish", "evaluate",
    "exacerbate", "exemplify", "facilitate", "fundamental", "generate",
    "hypothesis", "illustrate", "implication", "implement", "implicit",
    "incentive", "incorporate", "indicate", "inevitable", "infrastructure",
    "inherent", "innovation", "integrate", "interpret", "investigation",
    "justification", "legitimate", "magnitude", "manifest", "mechanism",
    "methodology", "mitigate", "nonetheless", "nuance", "obligation",
    "paradigm", "participate", "perceive", "perspective", "phenomenon",
    "pragmatic", "precedent", "predominant", "preliminary", "prevalent",
    "profound", "proliferate", "proposition", "rationale", "reinforce",
    "relevant", "resilient", "rhetoric", "rigorous", "scrutinize",
    "significant", "sophisticated", "subsequent", "substantial", "sustain",
    "synthesize", "tangible", "transparency", "undermine", "unprecedented",
    "validate", "viable", "vulnerable", "widespread",
}


def _tokenize_words(text: str) -> list:
    """Simple word tokenization."""
    return re.findall(r'\b[a-zA-Z]+\b', text.lower())


def _get_sentences(text: str) -> list:
    """Split text into sentences."""
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]


def _get_paragraphs(text: str) -> list:
    """Split text into paragraphs."""
    paragraphs = re.split(r'\n\s*\n|\n', text)
    return [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 10]


def _clamp(value: float, lo: float = 0.0, hi: float = 20.0) -> float:
    """Clamp a value to [lo, hi]."""
    return max(lo, min(hi, value))


# =====================
# Trait Scorers (each returns 0-20)
# =====================

def score_content_ideas(text: str, words: list, sentences: list) -> float:
    """
    Content & Ideas: measures depth and substance.
    Factors: word count, sentence count, idea density.
    """
    word_count = len(words)
    sent_count = len(sentences)

    # Word count score (essays <50 words penalized, >300 rewarded)
    if word_count < 30:
        wc_score = 4
    elif word_count < 100:
        wc_score = 8 + (word_count - 30) * 0.06
    elif word_count < 250:
        wc_score = 12 + (word_count - 100) * 0.04
    else:
        wc_score = 18

    # Sentence variety bonus
    if sent_count >= 5:
        wc_score += 1
    if sent_count >= 10:
        wc_score += 1

    return _clamp(round(wc_score, 1))


def score_organization(text: str, words: list, sentences: list, paragraphs: list) -> float:
    """
    Organization: measures structure and coherence.
    Factors: paragraph count, transition words, intro/conclusion.
    """
    score = 8.0  # base

    # Paragraph structure
    para_count = len(paragraphs)
    if para_count >= 3:
        score += 3
    elif para_count >= 2:
        score += 1.5

    # Transition word usage
    text_lower = text.lower()
    transition_count = sum(1 for tw in TRANSITION_WORDS if tw in text_lower)
    score += min(4, transition_count * 0.8)

    # Intro/conclusion detection
    if any(p in text_lower[:200] for p in ["i think", "i believe", "in my opinion", "the topic", "this essay"]):
        score += 1.5
    if any(p in text_lower[-200:] for p in ["in conclusion", "to summarize", "in summary", "overall", "finally"]):
        score += 1.5

    return _clamp(round(score, 1))


def score_language_use(text: str, words: list, sentences: list) -> float:
    """
    Language Use: measures grammatical variety and sophistication.
    Factors: sentence length variety, passive voice ratio, avg sentence length.
    """
    if not sentences:
        return 6.0

    score = 8.0

    # Sentence length variety
    sent_lengths = [len(s.split()) for s in sentences]
    if sent_lengths:
        avg_len = sum(sent_lengths) / len(sent_lengths)
        std_len = (sum((l - avg_len) ** 2 for l in sent_lengths) / len(sent_lengths)) ** 0.5

        # Reward variety
        if std_len > 3:
            score += 3
        elif std_len > 1.5:
            score += 1.5

        # Penalize very short or very long average
        if 10 <= avg_len <= 25:
            score += 3
        elif 7 <= avg_len <= 30:
            score += 1.5

    # Passive voice check (simple heuristic)
    passive_count = len(re.findall(r'\b(?:is|are|was|were|been|being)\s+\w+ed\b', text.lower()))
    passive_ratio = passive_count / max(1, len(sentences))
    if passive_ratio < 0.3:
        score += 2  # Some passive is ok, too much is bad

    return _clamp(round(score, 1))


def score_conventions(text: str) -> dict:
    """
    Conventions: grammar, spelling, punctuation.
    Uses LanguageTool for detailed error checking.
    Returns score (0-20) and list of grammar issues.
    """
    tool = _get_language_tool()
    matches = tool.check(text)

    # Filter out minor/style issues
    errors = []
    for match in matches:
        error_length = getattr(match, 'errorLength', getattr(match, 'length', 0))
        errors.append({
            "message": match.message,
            "context": match.context,
            "offset": match.offset,
            "length": error_length,
            "rule": match.rule_id,
            "replacements": match.replacements[:3] if match.replacements else [],
            "category": match.category,
        })

    error_count = len(errors)
    word_count = len(text.split())
    error_rate = error_count / max(1, word_count) * 100

    # Score: fewer errors = higher score
    if error_rate < 0.5:
        score = 18
    elif error_rate < 1.0:
        score = 16
    elif error_rate < 2.0:
        score = 14
    elif error_rate < 3.0:
        score = 12
    elif error_rate < 5.0:
        score = 10
    else:
        score = max(4, 20 - error_count)

    return {
        "score": _clamp(round(score, 1)),
        "error_count": error_count,
        "errors": errors[:20],  # Cap at 20 for response size
    }


def score_vocabulary(words: list) -> float:
    """
    Vocabulary: measures lexical richness and sophistication.
    Factors: type-token ratio, unique word %, advanced word usage.
    """
    if not words:
        return 6.0

    score = 6.0
    word_count = len(words)
    unique_words = set(words)
    unique_count = len(unique_words)

    # Type-token ratio (TTR)
    ttr = unique_count / word_count if word_count > 0 else 0
    if ttr > 0.7:
        score += 4
    elif ttr > 0.5:
        score += 2.5
    elif ttr > 0.35:
        score += 1

    # Advanced word usage
    advanced_used = unique_words & ADVANCED_WORDS
    advanced_ratio = len(advanced_used) / max(1, unique_count)
    if advanced_ratio > 0.05:
        score += 4
    elif advanced_ratio > 0.02:
        score += 2.5
    elif advanced_ratio > 0.01:
        score += 1

    # Word length variety
    avg_word_len = sum(len(w) for w in words) / max(1, word_count)
    if avg_word_len > 5.5:
        score += 3
    elif avg_word_len > 4.5:
        score += 2
    elif avg_word_len > 3.5:
        score += 1

    return _clamp(round(score, 1))


# =====================
# Readability & extra metrics
# =====================

def compute_readability(text: str) -> dict:
    """Compute readability metrics using textstat."""
    return {
        "flesch_reading_ease": textstat.flesch_reading_ease(text),
        "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
        "gunning_fog": textstat.gunning_fog(text),
        "automated_readability_index": textstat.automated_readability_index(text),
        "reading_time_seconds": textstat.reading_time(text, ms_per_char=14.69),
    }


def compute_analytics_metrics(text: str) -> dict:
    """
    Compute the 6 analytics metrics shown on the Analytics page.
    Each returns a percentage (0-100).
    """
    words = _tokenize_words(text)
    sentences = _get_sentences(text)
    paragraphs = _get_paragraphs(text)
    word_count = len(words)
    unique_words = set(words)

    # 1. Vocabulary Richness (unique words / total words * factor)
    vocab_richness = min(100, int((len(unique_words) / max(1, word_count)) * 130))

    # 2. Lexical Diversity (TTR adjusted)
    ttr = len(unique_words) / max(1, word_count)
    lexical_diversity = min(100, int(ttr * 140))

    # 3. Sentence Complexity (avg words per sentence, normalized)
    if sentences:
        avg_sent_len = sum(len(s.split()) for s in sentences) / len(sentences)
        sent_complexity = min(100, int((avg_sent_len / 25) * 100))
    else:
        sent_complexity = 30

    # 4. Paragraph Balance (std dev of paragraph lengths, lower is better)
    if len(paragraphs) >= 2:
        para_lens = [len(p.split()) for p in paragraphs]
        avg_para = sum(para_lens) / len(para_lens)
        std_para = (sum((l - avg_para) ** 2 for l in para_lens) / len(para_lens)) ** 0.5
        cv = std_para / max(1, avg_para)
        para_balance = max(30, min(100, int((1 - cv) * 100)))
    else:
        para_balance = 50

    # 5. Readability (Flesch reading ease, scaled)
    fre = textstat.flesch_reading_ease(text)
    readability = max(20, min(100, int(fre)))

    # 6. Repetition Detection (lower repetition = higher score)
    if word_count > 10:
        word_freq = Counter(words)
        # Words that appear more than 3 times (excluding common words)
        common_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                        "have", "has", "had", "do", "does", "did", "will", "would",
                        "could", "should", "may", "might", "can", "shall", "to", "of",
                        "in", "for", "on", "with", "at", "by", "from", "as", "into",
                        "and", "or", "but", "not", "that", "this", "it", "i", "you",
                        "he", "she", "we", "they", "my", "your", "his", "her", "its",
                        "our", "their", "what", "which", "who", "when", "where", "how"}
        repeated = sum(1 for w, c in word_freq.items()
                       if c > 3 and w not in common_words and len(w) > 3)
        rep_ratio = repeated / max(1, len(unique_words))
        repetition_score = max(30, min(100, int((1 - rep_ratio * 5) * 100)))
    else:
        repetition_score = 50

    return {
        "vocabulary_richness": vocab_richness,
        "lexical_diversity": lexical_diversity,
        "sentence_complexity": sent_complexity,
        "paragraph_balance": para_balance,
        "readability": readability,
        "repetition_detection": repetition_score,
    }


# =====================
# Main analysis function
# =====================

def analyze_essay(text: str) -> dict:
    """
    Full essay analysis. Returns trait scores, grammar errors, readability,
    and analytics metrics.
    """
    words = _tokenize_words(text)
    sentences = _get_sentences(text)
    paragraphs = _get_paragraphs(text)

    # Trait scores (each 0-20)
    content_score = score_content_ideas(text, words, sentences)
    org_score = score_organization(text, words, sentences, paragraphs)
    lang_score = score_language_use(text, words, sentences)
    conventions_result = score_conventions(text)
    vocab_score = score_vocabulary(words)

    # Writing consistency (compare paragraph-level scores)
    if len(paragraphs) >= 2:
        para_scores = []
        for p in paragraphs:
            pw = _tokenize_words(p)
            ps = _get_sentences(p)
            s = (score_content_ideas(p, pw, ps) + score_vocabulary(pw)) / 2
            para_scores.append(s)
        avg_ps = sum(para_scores) / len(para_scores)
        std_ps = (sum((s - avg_ps) ** 2 for s in para_scores) / len(para_scores)) ** 0.5
        consistency = max(30, min(100, int((1 - std_ps / 10) * 100)))
    else:
        consistency = 65

    traits = {
        "content_ideas": content_score,
        "organization": org_score,
        "language_use": lang_score,
        "conventions": conventions_result["score"],
        "vocabulary": vocab_score,
    }

    return {
        "traits": traits,
        "trait_total": round(sum(traits.values()), 1),
        "trait_max": 100,
        "grammar_errors": conventions_result["errors"],
        "grammar_error_count": conventions_result["error_count"],
        "readability": compute_readability(text),
        "analytics": compute_analytics_metrics(text),
        "writing_consistency": consistency,
        "word_count": len(text.split()),
        "char_count": len(text),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "unique_words": len(set(words)),
    }
