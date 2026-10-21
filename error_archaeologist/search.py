"""Relevance ranking: IDF-weighted fields + fuzzy signature matching."""

import difflib
import math

from .normalize import error_signature, extract_error_type, tokenize

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "to", "of", "in", "on",
    "for", "and", "or", "with", "this", "that", "it", "my", "i", "we",
    "you", "how", "why", "what", "fix",
}

FIELD_WEIGHTS = {
    "error": 5,
    "solution": 3,
    "attempted_fix": 3,
    "category": 2,
    "tags": 2,
    "language": 2,
    "explanation": 1,
}

SIGNATURE_WEIGHT = 12      # fuzzy match of normalised error text
ERROR_TYPE_BONUS = 4       # same exception class (TypeError == TypeError)
FUZZY_TOKEN_CREDIT = 0.6   # typo-tolerant token match counts partially


def _field_text(case, field):
    value = case.get(field, "")
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def case_tokens(case):
    """Tokens per field for one case."""
    return {field: tokenize(_field_text(case, field)) for field in FIELD_WEIGHTS}


def query_tokens(query):
    words = tokenize(query) - STOP_WORDS
    return words or tokenize(query)


def build_index(cases):
    """Pre-compute tokens, document frequency and vocabulary."""
    per_case = [case_tokens(case) for case in cases]
    doc_freq = {}
    for fields in per_case:
        seen = set().union(*fields.values()) if fields else set()
        for token in seen:
            doc_freq[token] = doc_freq.get(token, 0) + 1
    return per_case, doc_freq


def idf(token, doc_freq, total_docs):
    """Rare words matter more than words that appear in every case."""
    return math.log(1 + total_docs / (1 + doc_freq.get(token, 0)))


def score_case(case, query_words, doc_freq=None, total_docs=1,
               fields=None, query_text=""):
    """Score one case. Higher means more relevant."""
    doc_freq = doc_freq or {}
    fields = fields or case_tokens(case)
    score = 0.0

    for field, weight in FIELD_WEIGHTS.items():
        field_words = fields[field]
        for word in query_words:
            if word in field_words:
                score += weight * idf(word, doc_freq, total_docs)
            elif len(word) >= 5:
                close = difflib.get_close_matches(
                    word, field_words, n=1, cutoff=0.85
                )
                if close:
                    score += (weight * FUZZY_TOKEN_CREDIT
                              * idf(close[0], doc_freq, total_docs))

    if query_text:
        saved_error = case.get("error", "")
        ratio = difflib.SequenceMatcher(
            None, error_signature(query_text), error_signature(saved_error)
        ).ratio()
        if ratio >= 0.5:
            score += SIGNATURE_WEIGHT * ratio
        query_type = extract_error_type(query_text)
        if query_type and query_type == extract_error_type(saved_error):
            score += ERROR_TYPE_BONUS

    return round(score, 2)


def search(cases, query, language=None, limit=None):
    """Return [(score, case), ...] sorted best first."""
    if language:
        wanted = language.casefold()
        cases = [c for c in cases if str(c.get("language", "")).casefold() == wanted]
    if not cases or not str(query).strip():
        return []

    words = query_tokens(query)
    per_case, doc_freq = build_index(cases)
    total = len(cases)

    results = []
    for case, fields in zip(cases, per_case):
        value = score_case(case, words, doc_freq, total, fields, query)
        if value > 0:
            results.append((value, case))

    results.sort(
        key=lambda item: (item[0], str(item[1].get("timestamp", ""))),
        reverse=True,
    )
    return results[:limit] if limit else results
